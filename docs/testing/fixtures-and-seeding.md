# Fixtures And Seeding

Seed data must be deterministic so demos are repeatable.

PR 2 seeds ANC2 Batch 1 and Batch 2 into the workflow library. PR 3 adds an ANC2 experiment instance seeded from that workflow version.

PR 7 extends seed data with:

- additional local lab members for professor and postdoc roles
- a `general` channel
- an `anc2-purification` channel
- seeded ANC2 discussion messages that reference Batch 1 and Batch 2 workflows
