# Shared Lab Chat

PR 7 introduces a persisted local discussion surface for the lab.

## Purpose

The Teams page is not a generic social feed. It is a lab-scoped working surface for:

- workflow discussion
- experiment updates
- troubleshooting branches
- image evidence such as gels or chromatography screenshots

## Current Behavior

- Channels are visible only within the current `lab_id`.
- Messages persist to SQLite.
- Messages can reference a workflow template or experiment run.
- Messages can include image attachments.
- Refreshing the page reloads the same chat history from the backend.

## Moderation Rule

The message author can edit or delete their own message. Professors can also edit or delete messages from other lab members in local mode.
