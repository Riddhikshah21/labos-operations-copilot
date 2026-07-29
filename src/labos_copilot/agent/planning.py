"""Grounded AI planning for operational blocker remediation."""

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
from labos_copilot.agent.prompts import (
    ACTION_PLANNING_AGENT_INSTRUCTIONS,
)
from labos_copilot.agent.schemas import (
    ActionPlanningRunResult,
    ActionPlanSet,
)
from labos_copilot.agent.service import mcp_approval_policy
from labos_copilot.config import Settings
from labos_copilot.domain import (
    ActionType,
    BlockerCategory,
    BlockerFinding,
    Experiment,
)
from labos_copilot.rules import BlockerEngine
from labos_copilot.sdk import LabOSClient

_ALLOWED_ACTIONS: dict[
    BlockerCategory,
    frozenset[ActionType],
] = {
    BlockerCategory.DELAY: frozenset(
        {
            ActionType.REQUEST_OWNER_REVIEW,
            ActionType.PAUSE_EXPERIMENT,
            ActionType.WAIT_FOR_RESOURCE,
        }
    ),
    BlockerCategory.INVENTORY: frozenset(
        {
            ActionType.ESCALATE_MATERIAL_PROCUREMENT,
            ActionType.REQUEST_OWNER_REVIEW,
            ActionType.PAUSE_EXPERIMENT,
            ActionType.WAIT_FOR_RESOURCE,
        }
    ),
    BlockerCategory.INSTRUMENT: frozenset(
        {
            ActionType.REQUEST_INSTRUMENT_RESCHEDULE,
            ActionType.REQUEST_OWNER_REVIEW,
            ActionType.PAUSE_EXPERIMENT,
            ActionType.WAIT_FOR_RESOURCE,
        }
    ),
    BlockerCategory.DEADLINE: frozenset(
        {
            ActionType.ESCALATE_DELIVERY_RISK,
            ActionType.REQUEST_OWNER_REVIEW,
            ActionType.PAUSE_EXPERIMENT,
        }
    ),
}


def create_action_planning_agent(
    model_name: str,
    server: MCPServerStdio,
) -> Agent[None]:
    """Create the MCP-backed action-planning agent."""

    return Agent[None](
        name="LabOS Action Planner",
        instructions=ACTION_PLANNING_AGENT_INSTRUCTIONS,
        model=model_name,
        mcp_servers=[server],
        output_type=ActionPlanSet,
        model_settings=ModelSettings(
            tool_choice="required",
            parallel_tool_calls=False,
            store=False,
        ),
    )


def normalize_action_plan_evidence(
    plan: ActionPlanSet,
    experiment_id: str,
    rule_id: str,
) -> ActionPlanSet:
    """Attach mandatory grounding IDs to every candidate plan."""

    normalized_candidates = tuple(
        candidate.model_copy(
            update={
                "evidence_ids": tuple(
                    dict.fromkeys(
                        (
                            experiment_id,
                            rule_id,
                            *candidate.evidence_ids,
                        )
                    )
                )
            }
        )
        for candidate in plan.candidates
    )

    return plan.model_copy(update={"candidates": normalized_candidates})


def validate_action_plan(
    plan: ActionPlanSet,
    finding: BlockerFinding,
    experiment: Experiment,
) -> None:
    """Validate model-generated plans against deterministic state."""

    if plan.experiment_id != experiment.id:
        raise AgentGroundingError("The action plan references the wrong experiment.")

    if plan.source_rule_id != finding.rule_id:
        raise AgentGroundingError("The action plan references the wrong blocker rule.")

    if plan.category is not finding.category:
        raise AgentGroundingError("The action plan uses the wrong blocker category.")

    allowed_actions = _ALLOWED_ACTIONS[finding.category]

    allowed_evidence_ids = {
        experiment.id,
        finding.rule_id,
        *experiment.required_material_ids,
    }

    if experiment.required_instrument_id is not None:
        allowed_evidence_ids.add(experiment.required_instrument_id)

    if experiment.deadline_id is not None:
        allowed_evidence_ids.add(experiment.deadline_id)

    for candidate in plan.candidates:
        if candidate.action_type not in allowed_actions:
            raise AgentGroundingError(
                "The model selected an action that is not permitted "
                f"for category {finding.category.value!r}."
            )

        evidence_ids = set(candidate.evidence_ids)

        required_ids = {
            experiment.id,
            finding.rule_id,
        }

        if not required_ids.issubset(evidence_ids):
            raise AgentGroundingError("Every candidate must cite the experiment and blocker rule.")

        unsupported_ids = evidence_ids - allowed_evidence_ids

        if unsupported_ids:
            raise AgentGroundingError(
                f"The plan contains unsupported evidence IDs: {sorted(unsupported_ids)}"
            )


def _tool_was_used(
    tools_used: tuple[str, ...],
    required_name: str,
) -> bool:
    return any(tool_name.endswith(required_name) for tool_name in tools_used)


async def run_action_planning_agent(
    experiment_id: str,
    rule_id: str,
    settings: Settings,
    as_of: datetime | None = None,
) -> ActionPlanningRunResult:
    """Investigate one blocker and generate ranked action alternatives."""

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
        require_approval=mcp_approval_policy(),
        failure_error_function=None,
    ) as server:
        agent = create_action_planning_agent(
            settings.openai_model,
            server,
        )

        agent_input = (
            "Create two ranked remediation plans.\n\n"
            f"Experiment ID: {experiment_id}\n"
            f"Rule ID: {rule_id}\n"
            f"Analysis timestamp: {analysis_time.isoformat()}\n\n"
            "Investigate using MCP tools. Do not prepare or execute "
            "an action."
        )

        result = await Runner.run(
            agent,
            agent_input,
            max_turns=settings.agent_max_turns,
            run_config=RunConfig(
                tracing_disabled=True,
                trace_include_sensitive_data=False,
            ),
        )

        if result.interruptions:
            raise AgentProtocolError("The planning agent attempted an approval-gated action.")

        run_items = tuple(result.new_items)

    plan = ActionPlanSet.model_validate(result.final_output)

    tools_used = tuple(
        item.tool_name
        for item in run_items
        if isinstance(item, ToolCallItem) and item.tool_name is not None
    )

    if not _tool_was_used(
        tools_used,
        "analyze_experiment_blockers",
    ):
        raise AgentProtocolError("The planner did not analyze the experiment.")

    if not _tool_was_used(
        tools_used,
        "get_experiment_details",
    ):
        raise AgentProtocolError("The planner did not retrieve experiment context.")

    client = LabOSClient.from_fixture_directory(fixture_directory)

    analysis = BlockerEngine(client).analyze_experiment(
        experiment_id,
        analysis_time,
    )

    finding = next(
        (candidate for candidate in analysis.findings if candidate.rule_id == rule_id),
        None,
    )

    if finding is None:
        raise AgentGroundingError(
            f"No finding {rule_id!r} exists for experiment {experiment_id!r}."
        )

    category_tools = {
        BlockerCategory.INVENTORY: "get_inventory_status",
        BlockerCategory.INSTRUMENT: "get_instrument_status",
        BlockerCategory.DEADLINE: "get_customer_deadline",
    }

    required_category_tool = category_tools.get(finding.category)

    if required_category_tool is not None and not _tool_was_used(
        tools_used,
        required_category_tool,
    ):
        raise AgentProtocolError(
            f"The planner did not gather the required {finding.category.value} context."
        )

    experiment = client.experiments.get(experiment_id)

    plan = normalize_action_plan_evidence(
        plan=plan,
        experiment_id=experiment.id,
        rule_id=finding.rule_id,
    )

    validate_action_plan(
        plan=plan,
        finding=finding,
        experiment=experiment,
    )

    return ActionPlanningRunResult(
        model_name=settings.openai_model,
        analysis_time=analysis_time,
        plan=plan,
        tools_used=tools_used,
    )
