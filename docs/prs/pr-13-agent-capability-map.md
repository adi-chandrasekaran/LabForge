# PR 13: Agent Capability Map And Tool Contract

## Summary

Defines a versioned, non-executable agent-tool contract and a reviewable
capability map for the existing backend. It creates no LLM integration, MCP
transport, agent runtime, database table, API endpoint, or scientific analysis.

## Contract decisions

- All supported lookup/list/search tools are read-only.
- `create_note` is the only mapped write: it delegates to the existing chat
  message creation endpoint and is explicitly not an update to embedded notes.
- The future runtime must use the existing authenticated request context and
  retain backend authorization; it cannot take user, role, or lab scope as an
  input.
- The requested NMR-specific tools absent from the backend are catalogued as
  unavailable rather than stubbed or simulated.

## Automated verification

- `git diff --check`
- `python -m json.tool docs/contracts/agent-tool-contract.v1.json >/dev/null`
- `.venv/bin/python -m pytest backend/tests/test_ai_api.py backend/tests/test_experiment_api.py backend/tests/test_chat_api.py`

## Manual test

1. Compare every `supported` contract entry with its listed FastAPI route and
   confirm the input names, read/write classification, and result scope match.
2. Confirm `create_note` maps to creating a channel message and that its
   required `channel_id` and `body` prevent silent mutation of experiment or
   workflow-step note fields.
3. Confirm every unavailable requested NMR tool maps to an absent model and no
   placeholder analysis entry is described as an executable calculation.
4. Review the contract's shared-context rules and confirm that actor/lab/role
   are backend-derived rather than model-provided values.

## Manual merge

1. Merge this PR only after PR 12's domain audit is merged, or rebase it onto
   the resulting `main` commit before approval.
2. Require a backend review for operation/permission mappings and a lab-domain
   review for the unavailable NMR capability list.
3. Merge with a squash commit titled `docs: define agent capability map`.
