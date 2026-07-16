# Data Model

Core entities in the current implementation are `User`, `Project`, `Workflow`, `WorkflowStep`, `WorkflowBranch`, `Experiment`, `ExperimentWorkflowRun`, `ExperimentStepRun`, `ChatChannel`, `ChatMessage`, and `Attachment`.

## Workflow Library Shape

- `Workflow`
  - Reusable library template such as `ANC2 Batch 1` or `ANC2 Batch 2`.
  - Stores title, description, visibility, library state, version, and tags.
- `WorkflowStep`
  - Ordered mainline or branch step belonging to a workflow template.
  - Mainline steps have `workflow_branch_id = null`.
  - Branch steps belong to a `WorkflowBranch`.
- `WorkflowBranch`
  - Divergent troubleshooting or side-track anchored to a main workflow step through `anchor_step_id`.

## Experiment Run Shape

- `Experiment`
  - Dated run associated with a project and operator.
  - Top-level status reflects the aggregate state of the run.
- `ExperimentWorkflowRun`
  - Snapshot of a workflow template at experiment instantiation time.
  - Stores source workflow id plus copied workflow title, description, version, ordering, and run status.
- `ExperimentStepRun`
  - Snapshot of a workflow step at experiment instantiation time.
  - Stores source workflow step id plus copied step label, sublabel, duration, procedure, IO payloads, notes, and live run status.

## Step Payload Fields

Workflow steps and experiment step runs both store:

- `inputs`, `parameters`, and `outputs` as structured JSON for the schematic UI.
- `procedure_markdown` for the step procedure.
- `notes` for observations or protocol notes.
- `duration`, `label`, and `sublabel` for workflow rendering.
- attachment metadata lists in API reads, backed by the separate `Attachment` table.

Library-only step field:

- `status_template` defines the default state shown in the shared workflow library.

Experiment-only step field:

- `status` records what actually happened in that run.

## Separation Rules

- Workflows are reusable templates.
- Experiments are dated runs created from workflow versions.
- Editing an `ExperimentStepRun` must never mutate `WorkflowStep`.
- ANC2 Batch 1 and Batch 2 are seeded as templates and instantiated into separate workflow runs inside an experiment.
- Attachments can belong to either `workflow_step` or `experiment_step_run` owners.

## Shared Lab Chat Shape

- `ChatChannel`
  - Lab-scoped discussion container keyed by `lab_id`.
  - Stores name, topic, creator, and timestamps.
- `ChatMessage`
  - Individual persisted post inside a channel.
  - Stores author, message body, optional referenced workflow id, optional referenced experiment id, and timestamps.

## Attachment Ownership

The `Attachment` table now supports three owner types:

- `workflow_step`
- `experiment_step_run`
- `chat_message`

This keeps binary metadata uniform while allowing different UI surfaces to upload and render the same attachment shape.
