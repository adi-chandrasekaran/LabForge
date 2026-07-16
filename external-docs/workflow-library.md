# Workflow Library

The workflow library stores reusable lab procedures that students can instantiate into experiments.

## ANC2 Reference

ANC2 Batch 1 and Batch 2 are the reference workflows for the first library implementation.

- Batch 1: no refolding purification strategy.
- Batch 2: refolding protocol strategy.

## What Works Now

- Open the workflow page and view ANC2 from persisted backend data.
- Add a new step between existing steps or at the end of a workflow.
- Edit step labels, status, duration, procedure, inputs, parameters, outputs, and notes.
- Create one or more troubleshooting branches off a mainline step.
- Add steps inside a branch track.
- Refresh the page without losing those workflow edits.

## Current Limits

- The workflow page is the first API-backed screen. Other tabs still use prototype data and will be integrated in later PRs.
- Publish RBAC exists at the API layer. A dedicated publish control in the UI is not added yet.
