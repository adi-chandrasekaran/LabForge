# PR 16: Workflow draft review

Owners can now open `/workflow-drafts` to inspect their agent-generated workflow proposals. Pending drafts show their exact payload and require an explicit **Confirm and apply** click. The UI calls the existing single-use confirmation endpoint; it contains no automatic approval path.

The backend also provides `GET /api/v1/agent/workflow-drafts`, scoped to the authenticated owner, so the page never displays another user's proposals.
