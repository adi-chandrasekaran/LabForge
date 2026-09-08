# Experimental Workflows

The `Workflow` page is now for project-owned experimental workflows. These are editable working schematics for active projects.

## Project Tabs

The top of the page shows one tab per project.

Seeded examples:

- `ANC2`: two batch workflows shown once, side by side.
- `RPC10`: purification and troubleshooting workflow.
- `CCL20`: bacterial transformation and culture workflow.

When you create a new project, the app automatically creates a blank editable experimental workflow and adds a new project tab.

## What Works Now

- Open the `Workflow` page and switch between project tabs.
- Add a new step between existing steps or at the end of a workflow.
- Edit step labels, status, duration, procedure, inputs, parameters, outputs, and notes.
- Create one or more troubleshooting branches off a mainline step.
- Add steps inside a branch track.
- Insert an existing standardized workflow as copied editable steps.
- Standardize an experimental workflow into a reusable library workflow.
- Delete workflows, steps, and branches after confirmation.
- Refresh the page without losing those workflow edits.

## Standardizing An Experimental Workflow

1. Open `Workflow`.
2. Choose the project tab.
3. Scroll to the experimental workflow you want to reuse.
4. Click `Standardize`.
5. Enter a reusable workflow name, description, and tags.
6. Save it.
7. Open `Standardized` and confirm it appears in the reusable library.

## Inserting A Standardized Workflow

1. Open `Workflow`.
2. Choose the project tab.
3. Click `+ Add step` or create a branch.
4. Change `Source` from manual to `Standardized workflow`.
5. Choose Ion Exchange, Reverse Nickel, or another saved standardized workflow.
6. Insert it.
7. Edit the copied steps as part of the project workflow.
