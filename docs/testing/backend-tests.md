# Backend Tests

Run backend tests with:

```bash
.venv/bin/python -m pytest backend/tests
```

Current coverage includes:

- PR 1 foundation: health, OpenAPI, SQLite initialization, and mock current user behavior.
- PR 2 workflow library: ANC2 seed data, workflow CRUDL, step CRUDL, step reorder, branch creation, branch step creation, branch deletion, and publish RBAC.
- PR 3 experiments: experiment create/list/get/delete, ANC2 experiment instantiation, experiment step-run updates, persistence after reload, and workflow-template immutability.
- PR 4 attachments: workflow-step upload/list/delete/content, experiment-step upload/list/delete, invalid content type rejection, and attachment persistence through workflow and experiment serializers.
- PR 5 frontend integration backend slice: project list/create/read routes, duplicate-code validation, dashboard/profile summary routes, external-docs list/read routes, and OpenAPI exposure for those routes.
- PR 7 teams/chat: seeded chat visibility, channel CRUDL, message CRUDL, message image attachment upload/list, lab scoping, and author-vs-professor permission checks.
- PR 8 AI/MCP placeholders: AI settings contract, analysis module registry, MCP manifest generation from OpenAPI, and OpenAPI route discoverability for PR 8 endpoints.
