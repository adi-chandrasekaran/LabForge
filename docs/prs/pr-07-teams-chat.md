# PR 7: Teams, Chat, And Shared Lab Context

## Concept

This milestone introduces a Slack-like local lab discussion surface for workflows, experiments, and shared materials.

## Technical Details

- Add channels, messages, and message attachment models.
- Add lab-scoped message visibility.
- Add APIs for channel CRUDL, message CRUDL, and chat attachment upload/list.
- Reuse the shared attachment model for chat images with `owner_type = "chat_message"`.
- Wire the Teams page to persisted local API data with channel creation, message posting, references, and image upload.

## Testing Protocol

- Backend:
  - `.venv/bin/python -m pytest backend/tests/test_chat_api.py`
- Frontend build:
  - `npm run build`
- Playwright:
  - `PLAYWRIGHT_SKIP_WEBSERVER=1 PLAYWRIGHT_FRONTEND_PORT=4174 npm run test:e2e -- e2e/pr-07-teams-chat.spec.ts`
- Expected pass criteria:
  - channel CRUDL returns success codes
  - message attachment uploads are listed back on the same message
  - foreign-lab channels are hidden
  - non-author students cannot edit or delete another user's message
  - the Teams demo survives refresh without losing the created channel or message

## User-Facing How-To

Users can:

- open `/teams`
- create a channel for a workflow, troubleshooting track, or experiment
- post a persisted message
- optionally reference a workflow or experiment
- attach an image to the message
- refresh the page and see the channel history persist from SQLite

## Acceptance Checklist

- [x] Channel APIs.
- [x] Message APIs.
- [x] Message attachment support.
- [x] Teams page API integration.
- [x] Permission tests.
- [x] Playwright chat demo.
- [x] Docs and roadmap updates.

## Roadmap Update Note

`docs/roadmap.md` now marks PR 7 complete and records the shipped user-visible Teams experience.
