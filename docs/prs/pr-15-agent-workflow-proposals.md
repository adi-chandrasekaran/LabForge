# PR 15: Agent workflow proposals

The agent can now use `propose_workflow_change` during an authenticated agent run. The tool stores only an `AgentWorkflowDraft`, linked to that run and its conversation; it cannot confirm a draft or modify a workflow.

The tool supports creation, workflow metadata edits, step additions/edits/reorders, branch creation, and membership proposals. Its result tells the assistant which saved draft the owner must review through the existing confirmation endpoint.

The public direct tool-invocation endpoint intentionally rejects proposal creation without an agent-run context. `create_note` and every direct workflow write remain excluded from the provider function catalog.
