# PR 8: AI, MCP, And Analysis Placeholders

## Concept

This milestone reserves the AI and MCP architecture without pretending AI behavior exists before the underlying APIs are ready.

## Technical Details

- Added `backend/app/ai_routes.py` and mounted it under `/api/v1`.
- Added placeholder contract routes:
  - `GET /api/v1/ai/settings`
  - `GET /api/v1/analysis/modules`
  - `GET /api/v1/mcp/manifest`
- `GET /api/v1/mcp/manifest` is derived from the live FastAPI OpenAPI schema so future MCP conversion starts from the real HTTP contract.
- Added frontend API bindings and replaced the static `AIModelPage` with a backend-backed placeholder surface.
- The page now shows:
  - feature flags for chat, workflow builder, local models, API keys, and analysis modules
  - provider placeholders for OpenAI and Anthropic
  - local runtime placeholders for Ollama and llama.cpp
  - an analysis module registry preview
  - an MCP tool preview sourced from the live API schema
- All AI behavior remains explicitly disabled. No fake chat or simulated model output is shipped.

## Testing Protocol

- Backend:
  - `.venv/bin/python -m pytest backend/tests/test_ai_api.py backend/tests/test_foundation.py`
- Frontend build:
  - `npm run build`
- Playwright demo:
  - `PLAYWRIGHT_SKIP_WEBSERVER=1 PLAYWRIGHT_FRONTEND_PORT=5173 npm run test:e2e -- e2e/pr-08-ai-placeholders.spec.ts`
- Expected pass criteria:
  - AI settings route returns disabled placeholder flags.
  - Analysis module registry returns three placeholder modules.
  - MCP manifest includes real OpenAPI-derived routes such as `/api/v1/workflows` and `/api/v1/ai/settings`.
  - `/ai-model` loads without a frontend API error and renders provider/runtime/module/manifest sections.

## User-Facing How-To

1. Start backend: `npm run backend:watch`
2. Start frontend: `npm run dev`
3. Open `http://127.0.0.1:5173/ai-model`
4. Confirm the page renders:
   - AI settings summary
   - API provider placeholders
   - local runtime placeholders
   - analysis module registry
   - MCP tool preview
5. Confirm everything is labeled as placeholder or disabled rather than pretending to be operational.

## Acceptance Checklist

- [x] MCP placeholder endpoint.
- [x] AI settings placeholder.
- [x] Analysis module registry.
- [x] Contract tests.
- [x] Playwright AI placeholder demo.
- [x] AI/MCP docs.
- [x] Roadmap update.

## Roadmap Update Note

`docs/roadmap.md` now marks PR 8 complete and records the shipped placeholder API contracts, tests, and docs updates.
