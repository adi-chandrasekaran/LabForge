# ADR 0003: Attachment Storage Abstraction

Status: Accepted

Attachment records store metadata independently from file storage and are retrieved through stable API routes rather than direct file-path references.

Consequences:

- Local mode can use `data/uploads`.
- Hosted mode can use Tigris without changing workflow or experiment schemas.
- Attachments need owner type and owner id fields.
- The API can expose a download URL while keeping storage implementation private.
- Workflow and experiment step serializers can embed attachment metadata without embedding binary content.
