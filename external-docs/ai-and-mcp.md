# AI And MCP

The AI page in NMR Lab is a contract placeholder, not an active model surface.

## What You Can See Today

Open `/ai-model` to inspect:

- AI settings flags
- future API key provider slots
- future local model runtime slots
- analysis module placeholders
- an MCP-oriented manifest preview derived from the live API

## What Is Not Active Yet

These features are intentionally not implemented yet:

- chat with an AI assistant
- workflow generation by agent
- automatic result interpretation
- local model execution
- API key storage and provider calls
- analysis module execution

## Why This Page Exists

The page fixes the contract before behavior is added.

That means later AI work can:

- reuse stable backend routes
- reuse a stable frontend data shape
- build MCP tooling from the real OpenAPI contract
- add execution without redesigning the page again

## How To Read The MCP Section

The MCP preview is not a live MCP server. It is a placeholder manifest showing which API routes could later be exposed as tools for an AI agent.

## What To Expect Next

Future milestones may add:

- secure settings for API keys
- local runtime discovery
- model provider selection
- chat orchestration
- workflow-building agents
- real analysis modules with saved outputs
