"""Streamlit interface for LabOS Operations Copilot."""

import asyncio
from datetime import UTC, date, datetime, time

import streamlit as st

from labos_copilot.actions import (
    ActionPreparationError,
    ActionService,
)
from labos_copilot.agent.errors import OperationsAgentError
from labos_copilot.agent.schemas import (
    AgentRunResult,
    BriefItem,
)
from labos_copilot.agent.service import (
    run_daily_operations_agent,
)
from labos_copilot.config import Settings
from labos_copilot.domain import Severity
from labos_copilot.rules import BlockerEngine
from labos_copilot.sdk import LabOSClient
from labos_copilot.ui import (
    all_brief_items,
    find_brief_item,
    finding_counts,
    finding_key,
    finding_label,
)

DEMO_DATE = date(2026, 7, 26)
DEMO_TIME = time(0, 0)


def initialize_session_state() -> None:
    """Initialize application state used across Streamlit reruns."""

    defaults = {
        "agent_result": None,
        "analysis_time": None,
        "pending_finding_key": None,
        "completed_action": None,
        "action_message": None,
        "last_error": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_review_state() -> None:
    """Clear the previous review and action state."""

    st.session_state.agent_result = None
    st.session_state.analysis_time = None
    st.session_state.pending_finding_key = None
    st.session_state.completed_action = None
    st.session_state.action_message = None
    st.session_state.last_error = None


def run_agent_review(
    question: str,
    settings: Settings,
    analysis_time: datetime,
) -> AgentRunResult:
    """Execute the asynchronous agent from Streamlit."""

    return asyncio.run(
        run_daily_operations_agent(
            question=question,
            settings=settings,
            as_of=analysis_time,
        )
    )


def create_action_service(
    settings: Settings,
    analysis_time: datetime,
) -> ActionService:
    """Create an action service using the same review timestamp."""

    client = LabOSClient.from_fixture_directory(settings.labos_fixtures_dir.resolve())

    return ActionService(
        engine=BlockerEngine(client),
        now_provider=lambda: analysis_time,
    )


def render_finding(item: BriefItem) -> None:
    """Render one blocker finding."""

    label = finding_label(item)

    with st.expander(label):
        st.markdown(f"**Summary:** {item.summary}")

        st.markdown("**Evidence:**")

        for evidence in item.evidence:
            st.markdown(f"- {evidence}")

        st.markdown(f"**Recommended action:** {item.recommended_action}")


def render_findings(
    items: tuple[BriefItem, ...],
    empty_message: str,
) -> None:
    """Render a collection of blocker findings."""

    if not items:
        st.success(empty_message)
        return

    for item in items:
        render_finding(item)


def render_dashboard(result: AgentRunResult) -> None:
    """Render metrics and the structured operations brief."""

    brief = result.brief
    counts = finding_counts(brief)

    metric_columns = st.columns(4)

    metric_columns[0].metric(
        "Experiments reviewed",
        brief.experiments_reviewed,
    )

    metric_columns[1].metric(
        "Critical findings",
        counts[Severity.CRITICAL],
    )

    metric_columns[2].metric(
        "Warnings",
        counts[Severity.WARNING],
    )

    metric_columns[3].metric(
        "Healthy experiments",
        len(brief.healthy_experiment_ids),
    )

    st.subheader("Operations summary")
    st.write(brief.executive_summary)

    st.markdown(f"**Recommended next action:** {brief.recommended_next_action}")

    critical_tab, warning_tab, healthy_tab, trace_tab = st.tabs(
        [
            "Critical",
            "Warnings",
            "Healthy",
            "Agent trace",
        ]
    )

    with critical_tab:
        render_findings(
            brief.critical_items,
            "No critical findings.",
        )

    with warning_tab:
        render_findings(
            brief.warning_items,
            "No warning findings.",
        )

    with healthy_tab:
        if brief.healthy_experiment_ids:
            for experiment_id in brief.healthy_experiment_ids:
                st.markdown(f"- `{experiment_id}`")
        else:
            st.info("No experiments were classified as healthy at this analysis time.")

    with trace_tab:
        st.markdown(f"**Model:** `{result.model_name}`")

        st.markdown("**MCP tools used:**")

        for tool_name in result.tools_used:
            st.markdown(f"- `{tool_name}`")

        if result.approval_decisions:
            st.markdown("**Agent approval decisions:**")

            for decision in result.approval_decisions:
                status = "approved" if decision.approved else "rejected"

                st.markdown(f"- `{decision.tool_name}`: {status}")


def render_action_panel(
    result: AgentRunResult,
    settings: Settings,
) -> None:
    """Render the explicit mock-action approval workflow."""

    st.divider()
    st.subheader("Mock operations action")

    st.caption(
        "The selected action is created only after explicit "
        "approval. No external system is modified."
    )

    items = all_brief_items(result.brief)

    if not items:
        st.info("No blocker findings are available for action.")
        return

    labels_to_keys = {finding_label(item): finding_key(item) for item in items}

    selected_label = st.selectbox(
        "Select a validated finding",
        options=list(labels_to_keys),
    )

    selected_key = labels_to_keys[selected_label]

    if st.button("Prepare mock action"):
        st.session_state.pending_finding_key = selected_key
        st.session_state.completed_action = None
        st.session_state.action_message = None

    pending_key = st.session_state.pending_finding_key

    if pending_key is not None:
        pending_item = find_brief_item(
            result.brief,
            pending_key,
        )

        st.warning("Approval required")

        st.markdown(f"**Experiment:** `{pending_item.experiment_id}`")
        st.markdown(f"**Source rule:** `{pending_item.rule_id}`")
        st.markdown(f"**Proposed action:** {pending_item.recommended_action}")

        approve_column, reject_column = st.columns(2)

        if approve_column.button(
            "Approve mock action",
            type="primary",
        ):
            analysis_time = st.session_state.analysis_time

            if analysis_time is None:
                st.error("The analysis timestamp is unavailable.")
                return

            try:
                action_service = create_action_service(
                    settings,
                    analysis_time,
                )

                action = action_service.prepare(
                    experiment_id=(pending_item.experiment_id),
                    rule_id=pending_item.rule_id,
                    as_of=analysis_time,
                )

                st.session_state.completed_action = action
                st.session_state.pending_finding_key = None
                st.session_state.action_message = "Mock action approved and completed."

                st.rerun()

            except ActionPreparationError as exc:
                st.error(str(exc))

        if reject_column.button("Reject"):
            st.session_state.pending_finding_key = None
            st.session_state.completed_action = None
            st.session_state.action_message = "Mock action rejected. Nothing was executed."

            st.rerun()

    action_message = st.session_state.action_message

    if action_message:
        st.info(action_message)

    completed_action = st.session_state.completed_action

    if completed_action is not None:
        st.success(f"Created mock action `{completed_action.id}`.")

        st.json(completed_action.model_dump(mode="json"))


def main() -> None:
    """Render the application."""

    st.set_page_config(
        page_title="LabOS Operations Copilot",
        page_icon="🧪",
        layout="wide",
    )

    initialize_session_state()
    settings = Settings()

    st.title("LabOS Operations Copilot")

    st.caption("MCP-backed AI orchestration with deterministic laboratory blocker analysis.")

    with st.sidebar:
        st.header("Daily review")

        with st.form("review_form"):
            question = st.text_area(
                "Operations question",
                value=("Which experiments need attention today?"),
                height=100,
            )

            review_date = st.date_input(
                "Analysis date",
                value=DEMO_DATE,
            )

            review_time = st.time_input(
                "Analysis time (UTC)",
                value=DEMO_TIME,
            )

            submitted = st.form_submit_button(
                "Run AI review",
                type="primary",
            )

        if st.button("Clear session"):
            clear_review_state()
            st.rerun()

    if submitted:
        analysis_time = datetime.combine(
            review_date,
            review_time,
            tzinfo=UTC,
        )

        clear_review_state()

        status = st.status(
            "Running MCP-backed AI review...",
            expanded=True,
        )

        try:
            status.write(f"Starting model `{settings.openai_model}`.")
            status.write("Connecting to the local LabOS MCP server.")
            status.write("Running deterministic blocker analysis.")

            result = run_agent_review(
                question=question,
                settings=settings,
                analysis_time=analysis_time,
            )

            st.session_state.agent_result = result
            st.session_state.analysis_time = analysis_time

            status.update(
                label="Review complete",
                state="complete",
                expanded=False,
            )

        except (
            OperationsAgentError,
            ValueError,
            RuntimeError,
        ) as exc:
            st.session_state.last_error = f"{type(exc).__name__}: {exc}"

            status.update(
                label="Review failed",
                state="error",
                expanded=True,
            )

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    result = st.session_state.agent_result

    if result is None:
        st.info("Configure the analysis in the sidebar and run the AI review.")
        return

    render_dashboard(result)
    render_action_panel(result, settings)


if __name__ == "__main__":
    main()
