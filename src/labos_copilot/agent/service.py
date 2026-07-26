"""OpenAI Agents SDK orchestration for LabOS operations."""

import os
import sys
from datetime import UTC, datetime

from agents import (
    Agent,
    ModelSettings,
    RunConfig,
    Runner,
    set_default_openai_key,
)
from agents.items import ToolCallItem
from agents.mcp import MCPServerStdio

from labos_copilot.agent.errors import (
    AgentGroundingError,
    AgentProtocolError,
)
from labos_copilot.agent.grounding import validate_daily_brief
from labos_copilot.agent.prompts import OPERATIONS_AGENT_INSTRUCTIONS
from labos_copilot.agent.schemas import (
    AgentRunResult,
    BriefItem,
    OperationsBrief,
    OperationsNarrative,
)
from labos_copilot.config import Settings
from labos_copilot.domain import (
    ExperimentBlockerAnalysis,
    Severity,
)
from labos_copilot.rules import BlockerEngine
from labos_copilot.sdk import LabOSClient


def create_operations_agent(
    model_name: str,
    server: MCPServerStdio,
) -> Agent[None]:
    """Create the LabOS operations agent."""

    return Agent[None](
        name="LabOS Operations Copilot",
        instructions=OPERATIONS_AGENT_INSTRUCTIONS,
        model=model_name,
        mcp_servers=[server],
        output_type=OperationsNarrative,
        model_settings=ModelSettings(
            tool_choice="required",
            parallel_tool_calls=False,
            store=False,
        ),
    )


def build_operations_brief(
    narrative: OperationsNarrative,
    analyses: list[ExperimentBlockerAnalysis],
    analysis_time: datetime,
) -> OperationsBrief:
    """Build factual brief content from deterministic findings."""

    # Flatten findings from every experiment analysis into one list.
    findings = [finding for analysis in analyses for finding in analysis.findings]

    critical_items = tuple(
        BriefItem(
            rule_id=finding.rule_id,
            experiment_id=finding.experiment_id,
            category=finding.category,
            severity=finding.severity,
            summary=finding.summary,
            evidence=finding.evidence,
            recommended_action=finding.recommended_action,
        )
        for finding in findings
        if finding.severity is Severity.CRITICAL
    )

    warning_items = tuple(
        BriefItem(
            rule_id=finding.rule_id,
            experiment_id=finding.experiment_id,
            category=finding.category,
            severity=finding.severity,
            summary=finding.summary,
            evidence=finding.evidence,
            recommended_action=finding.recommended_action,
        )
        for finding in findings
        if finding.severity is Severity.WARNING
    )

    healthy_experiment_ids = tuple(
        analysis.experiment_id for analysis in analyses if analysis.is_healthy
    )

    if findings:
        priority_finding = next(
            (
                finding
                for finding in findings
                if (
                    finding.experiment_id == narrative.priority_experiment_id
                    and finding.rule_id == narrative.priority_rule_id
                )
            ),
            None,
        )

        if priority_finding is None:
            raise AgentGroundingError("The agent selected an unsupported priority finding.")

        recommended_next_action = priority_finding.recommended_action

    else:
        if narrative.priority_experiment_id is not None or narrative.priority_rule_id is not None:
            raise AgentGroundingError(
                "The agent selected a priority finding when no findings exist."
            )

        recommended_next_action = "No action required."

    return OperationsBrief(
        generated_at=analysis_time,
        experiments_reviewed=len(analyses),
        executive_summary=build_executive_summary(analyses),
        critical_items=critical_items,
        warning_items=warning_items,
        healthy_experiment_ids=healthy_experiment_ids,
        recommended_next_action=recommended_next_action,
    )


async def run_daily_operations_agent(
    question: str,
    settings: Settings,
    as_of: datetime | None = None,
) -> AgentRunResult:
    """Run the MCP-backed agent and validate its output."""

    normalized_question = question.strip()

    if not normalized_question:
        raise ValueError("Question must not be empty.")

    if settings.openai_api_key is None:
        raise AgentProtocolError("OPENAI_API_KEY is missing.")

    analysis_time = as_of or datetime.now(UTC).replace(microsecond=0)

    if analysis_time.tzinfo is None or analysis_time.utcoffset() is None:
        raise ValueError("Analysis time must be timezone-aware.")

    set_default_openai_key(settings.openai_api_key.get_secret_value())

    fixture_directory = settings.labos_fixtures_dir.resolve()

    server_environment = dict(os.environ)
    server_environment["LABOS_FIXTURES_DIR"] = str(fixture_directory)
    server_environment["LABOS_ANALYSIS_TIME"] = analysis_time.isoformat()

    async with MCPServerStdio(
        name="LabOS MCP Server",
        params={
            "command": sys.executable,
            "args": [
                "-m",
                "labos_copilot.mcp.server",
            ],
            "env": server_environment,
        },
        cache_tools_list=True,
        client_session_timeout_seconds=30,
        require_approval="never",
        failure_error_function=None,
    ) as server:
        agent = create_operations_agent(
            settings.openai_model,
            server,
        )

        agent_input = (
            f"{normalized_question}\n\n"
            f"Analysis timestamp: {analysis_time.isoformat()}\n"
            "Call analyze_active_experiments using this "
            "exact timestamp."
        )

        result = await Runner.run(
            agent,
            agent_input,
            max_turns=settings.agent_max_turns,
            run_config=RunConfig(
                trace_include_sensitive_data=False,
            ),
        )

    # The LLM produces only narrative and priority selection.
    narrative = OperationsNarrative.model_validate(result.final_output)

    tools_used = tuple(
        item.tool_name
        for item in result.new_items
        if isinstance(item, ToolCallItem) and item.tool_name is not None
    )

    if not any(tool_name.endswith("analyze_active_experiments") for tool_name in tools_used):
        raise AgentProtocolError("The agent did not call analyze_active_experiments.")

    # Python independently runs the deterministic analysis.
    client = LabOSClient.from_fixture_directory(fixture_directory)

    analyses = BlockerEngine(client).analyze_active(analysis_time)

    # Python constructs every factual finding.
    brief = build_operations_brief(
        narrative=narrative,
        analyses=analyses,
        analysis_time=analysis_time,
    )

    validate_daily_brief(
        brief=brief,
        analyses=analyses,
        as_of=analysis_time,
    )

    return AgentRunResult(
        question=normalized_question,
        model_name=settings.openai_model,
        brief=brief,
        tools_used=tools_used,
    )


def build_executive_summary(
    analyses: list[ExperimentBlockerAnalysis],
) -> str:
    """Create a factual summary from deterministic findings."""

    findings = [finding for analysis in analyses for finding in analysis.findings]

    affected_ids = {finding.experiment_id for finding in findings}

    critical_count = sum(finding.severity is Severity.CRITICAL for finding in findings)

    warning_count = sum(finding.severity is Severity.WARNING for finding in findings)

    healthy_count = sum(analysis.is_healthy for analysis in analyses)

    return (
        f"Reviewed {len(analyses)} active experiments. "
        f"{len(affected_ids)} require attention, with "
        f"{critical_count} critical findings and "
        f"{warning_count} warnings. "
        f"{healthy_count} have no detected blockers."
    )
