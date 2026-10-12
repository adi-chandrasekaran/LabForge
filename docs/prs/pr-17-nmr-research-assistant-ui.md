# PR 17: NMR research assistant UI

This adds the user-facing **ASSISTANT** page in the LabForge sidebar. It uses the existing conversation/run API, displays provider availability before sending a message, and renders the assistant answer together with a collapsible ordered tool audit.

The UI matches the existing application’s compact mono typography, bordered panels, muted metadata, and teal/violet safety accents. It never exposes provider secrets. If the provider is unavailable or a request fails, it shows the server’s safe error rather than inventing an answer.

Any workflow draft prepared by the agent remains pending and must be reviewed through **DRAFT REVIEWS**.
