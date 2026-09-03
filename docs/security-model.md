# Security Model

## What's Protected

E-Version handles your most personal context — documents, infrastructure details, relationships, credentials. The security model ensures this data stays private, isolated, and under your control at every layer.

1. **Credentials are structurally protected** — only references are stored (vault paths, key names), never raw values.
2. **Sensitive values stay out of prompts** — redacted before any LLM call.
3. **Tenant isolation is structural** — every query, every store, every retrieval is scoped.
4. **Permissions flow from source to answer** — the assistant surfaces only what the active context can see.
5. **Audit logs are append-only** — every significant action is recorded and exportable.
6. **Local-first deployment is supported** — for full data sovereignty.

---

## Credential Handling

### Stored as references
- A **reference** to the secret (vault path, key name, environment variable name)
- Metadata about the secret (type, when rotated, who owns it)

### Structurally protected
Passwords, API keys, tokens, private keys, and connection strings with embedded credentials are detected and handled as references — the raw values stay in your secrets manager where they belong.

### Detection
The `SensitivityPolicyEngine` scans ingested documents for accidental secrets using pattern matching. Matched documents are:
- Flagged for user review
- Held from the retrieval index until reviewed
- Kept out of LLM prompts

---

## Authentication

- JWT-based authentication at the API Gateway
- Tokens signed with a secret stored in the secrets manager
- Tokens include `tenant_id`, `user_id`, and `roles`
- Token expiry: 1 hour (access), 30 days (refresh)
- All API requests require a valid JWT

---

## Tenant Isolation

- Every database record is scoped to `tenant_id` + `user_id`
- All queries include `WHERE tenant_id = $1 AND user_id = $2`
- Cross-tenant access is structurally prevented at the service layer
- No shared state between tenants in Redis or object store

---

## Data Encryption

- **At rest:** Postgres data encrypted at the volume level (provider-managed or LUKS)
- **pgvector embeddings:** Stored in encrypted Postgres volumes
- **Object store:** MinIO with server-side encryption (SSE-S3 or SSE-KMS)
- **In transit:** TLS 1.3 required for all service-to-service and client-to-service communication

---

## Local-First Mode

For maximum privacy and data sovereignty:
- All services run locally via Docker Compose
- No data leaves the local machine unless you configure a cloud LLM
- Optional: use a local LLM (Ollama, LM Studio) for fully air-gapped operation
- Object store (MinIO) replaces cloud blob storage
- Meilisearch replaces cloud search

---

## Sensitive Data in Prompts

The Sensitivity Policy Engine ensures:
- Sensitive pattern detection before any content enters a prompt
- Automatic redaction of matched values (replaced with `[REDACTED]`)
- CredentialReference entities are referenced by name only

Example safe prompt inclusion:
```
The router admin account is referenced as [router_admin_credentials].
Retrieve the actual value from your secrets manager before connecting.
```

---

## Audit Log

Every significant action is recorded in the `audit_events` table:

| Action | Resource Type | Logged |
|--------|--------------|--------|
| user.login | user | yes |
| user.logout | user | yes |
| session.create | session | yes |
| session.query | session | yes |
| memory.promote | memory | yes |
| memory.delete | memory | yes |
| source.ingest | source | yes |
| source.delete | source | yes |
| policy.create | policy | yes |
| policy.hold | resource | yes |
| sensitivity.flag | document | yes |

Audit logs are:
- Append-only
- Indexed by tenant and timestamp
- Exportable by the user
- Retained for 90 days minimum

---

## Your Data Rights

You can at any time:
- Export all your data (documents, chunks, facts, memories, sessions)
- Delete specific memories or all memories
- Delete your account and all associated data
- Inspect which sources are indexed and what facts were derived
- View the full retrieval trace for any past answer
