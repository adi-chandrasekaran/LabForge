# Experiment Runs

An experiment run records what actually happened on a given day.

## Core Idea

Workflow templates describe the shared protocol. Experiment runs record execution of that protocol for a specific project, date, and operator.

## Current Implementation

- An `Experiment` is created directly or instantiated from one or more workflow templates.
- Each instantiated workflow becomes an `ExperimentWorkflowRun`.
- Each mainline step in that workflow becomes an `ExperimentStepRun`.
- Experiment step runs are editable without changing the source workflow step.

## ANC2 Reference

The ANC2 placeholder project instantiates two workflow runs in one experiment:

- `ANC2 Batch 1`
- `ANC2 Batch 2`

This allows users to compare native-condition and refolding strategies inside the same dated experiment while preserving the workflow library.

## Why This Split Matters

- Students can log actual outcomes, delays, and notes.
- Professors and postdocs can revise the shared workflow library later.
- Historical experiment records remain reproducible because they retain the copied workflow structure used at the time of the run.
