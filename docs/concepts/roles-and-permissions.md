# Roles And Permissions

Roles control who can publish workflows to the shared library and how shared lab chat moderation works.

Professors, post docs, and phd users can publish. Students and interns can create private workflows and experiments. Hosted auth will come from Supabase; local mode uses a mock user.

In PR 7 chat behavior:

- any local lab member can create channels and post messages
- chat visibility is constrained to the current `lab_id`
- message edits and deletes are allowed for the original author
- professors can override and edit or delete another lab member's message when moderation is needed
