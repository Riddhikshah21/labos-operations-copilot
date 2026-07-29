from labos_copilot.agent.planning import (
    normalize_action_plan_evidence,
)
from labos_copilot.agent.schemas import (
    ActionPlanCandidate,
    ActionPlanSet,
    ActionUrgency,
)
from labos_copilot.domain import (
    ActionType,
    BlockerCategory,
)


def test_normalize_action_plan_evidence_adds_required_ids() -> None:
    """Mandatory grounding identifiers are added deterministically."""

    candidate = ActionPlanCandidate(
        plan_id="PLAN-1",
        action_type=ActionType.ESCALATE_MATERIAL_PROCUREMENT,
        title="Escalate procurement",
        rationale="The required material is unavailable.",
        operational_steps=("Contact procurement.",),
        expected_impact="Reduce material-related delay.",
        tradeoffs=("Procurement lead time remains uncertain.",),
        urgency=ActionUrgency.TODAY,
        confidence=0.85,
        evidence_ids=("MAT-003", "inventory-record"),
    )

    plan = ActionPlanSet(
        experiment_id="EXP-103",
        source_rule_id="inventory-out-of-stock",
        category=BlockerCategory.INVENTORY,
        candidates=(
            candidate,
            candidate.model_copy(
                update={
                    "plan_id": "PLAN-2",
                    "action_type": ActionType.PAUSE_EXPERIMENT,
                }
            ),
        ),
        recommended_plan_id="PLAN-1",
        selection_rationale="Procurement has the best recovery potential.",
    )

    normalized = normalize_action_plan_evidence(
        plan=plan,
        experiment_id="EXP-103",
        rule_id="inventory-out-of-stock",
    )

    for normalized_candidate in normalized.candidates:
        assert "EXP-103" in normalized_candidate.evidence_ids
        assert "inventory-out-of-stock" in normalized_candidate.evidence_ids
