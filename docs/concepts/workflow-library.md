# Workflow Library

The workflow library stores reusable procedures students can instantiate into experiments.

## Current Behavior

PR 2 ships the first persisted library implementation:

- ANC2 Batch 1 is seeded as a native purification workflow.
- ANC2 Batch 2 is seeded as a refolding workflow.
- Each workflow step can be created, edited, deleted, and reordered through the API.
- Troubleshooting branches are stored as first-class branch tracks anchored to a main step.

## Authoring Model

Workflow authors define:

- Step labels and sublabels.
- Step procedures.
- Inputs, parameters, and outputs.
- Template notes.
- Troubleshooting branch tracks.

Publishing to the shared library is gated by RBAC. In the current local mode, the mock professor user can publish and students/interns cannot.
