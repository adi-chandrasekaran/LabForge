# Auth And RBAC

Local mode uses a mock current user through an auth adapter. Hosted mode will replace this with a Supabase-backed adapter without changing route code.

Current auth backends:

- `mock`: implemented and used for local development.
- `supabase`: declared as a placeholder and intentionally returns `501 Not Implemented` if selected before hosted auth is built.

Planned roles:

- `professor`
- `post_doc`
- `phd`
- `student`
- `intern`

Workflow library publishing is limited to professor, post_doc, and phd roles. Students and interns can create private workflows and experiments, but cannot publish to the shared library.
