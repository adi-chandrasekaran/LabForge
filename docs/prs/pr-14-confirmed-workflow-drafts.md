# PR 14: Confirmed workflow drafts

The assistant may prepare a bounded workflow-change draft, but it cannot apply a workflow edit itself. Drafts are owner-scoped, tied to an optional agent conversation/run, immutable in their requested payload, expire after 24 hours, and record their eventual outcome.

`POST /api/v1/agent/workflow-drafts` prepares one proposal. The owner reviews it and calls `POST /api/v1/agent/workflow-drafts/{draft_id}/confirm` to apply exactly that draft once. Confirmation checks ownership, expiry, edit permission, and that the affected workflow has not changed since the draft was created.

Supported operations are workflow creation, workflow metadata changes, main-step addition and edits, reordering, branch creation, and membership replacement. Direct workflow writes remain existing application operations; this endpoint provides the explicit human confirmation boundary for future agent proposals.

No provider key, model write capability, or automatic confirmation is introduced.
