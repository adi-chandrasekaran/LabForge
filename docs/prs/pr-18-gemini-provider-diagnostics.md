# PR 18: Gemini provider diagnostics

The Assistant page now has a **Test Gemini connection** action. It calls a minimal server-side provider preflight only when the authenticated user requests it.

Failures are classified into safe, actionable codes: invalid API key, project permission denial, quota exhaustion, model unavailability, or a generic provider-request failure. The UI and logs never expose an API key or raw Google error response.

This is a diagnostic, not a billing or provisioning feature. A valid Google AI Studio key and an allowed Google project are still required for real model execution.
