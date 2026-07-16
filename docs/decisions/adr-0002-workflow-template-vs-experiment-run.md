# ADR 0002: Workflow Template Vs Experiment Run

Status: Accepted

Reusable workflows and daily experiment runs are separate data concepts.

Consequences:

- Editing an experiment does not mutate the shared workflow template.
- Experiments store workflow version references and step-run observations.
- The app can compare expected procedure against actual outcomes.
