# Evaluation Report

Generated: `2026-07-26T22:00:37.428249+00:00`

## Offline Metrics

| Metric | Result |
|---|---:|
| Case pass rate | 9/9 (100.0%) |
| Finding precision | 100.0% |
| Finding recall | 100.0% |
| Missing findings | 0 |
| Unexpected findings | 0 |

## Offline Cases

| Case | Type | Result | Details |
|---|---|---|---|
| `healthy-experiment` | analysis | **PASS** | No blocker findings. |
| `delayed-experiment` | analysis | **PASS** | stage-delay:delay:critical |
| `missing-material` | analysis | **PASS** | inventory-out-of-stock:inventory:critical |
| `instrument-maintenance` | analysis | **PASS** | instrument-maintenance:instrument:critical |
| `multiple-blockers` | analysis | **PASS** | deadline-risk:deadline:critical; instrument-offline:instrument:critical; inventory-below-minimum:inventory:warning; stage-delay:delay:critical |
| `unknown-experiment` | analysis | **PASS** | Observed expected error: ResourceNotFoundError |
| `inventory-action` | action | **PASS** | action_type=escalate_material_procurement; status=mock_completed |
| `deadline-action` | action | **PASS** | action_type=escalate_delivery_risk; status=mock_completed |
| `invalid-action` | action | **PASS** | Observed expected error: ActionPreparationError |

## Interpretation

Offline cases validate deterministic blocker classification and mock-action policy.
Live cases, when enabled, validate MCP tool selection and approval behavior using the configured LLM.
