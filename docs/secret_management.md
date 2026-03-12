# Secret Management

The GCO-Engine handles secrets using environment-driven configuration to ensure security in production.

## Key Principles

1. **No Plaintext Secrets:**
   - Plaintext secrets must NEVER be committed to the repository.
   - Use `.env.example` as a template for environment variables.
   - For production, use a secure secret management service (e.g., HashiCorp Vault, AWS Secrets Manager).

2. **Sanitized Configuration:**
   - Configuration endpoints (e.g., `/ot/config`) must always sanitize secrets (e.g., replacing passwords with `********`) before returning them.

3. **Log Sanitization:**
   - Sensitive information, such as passwords or JWTs, must never be printed to application logs.

## Critical Secrets

- `GATEWAY_JWT_SECRET`: The primary secret used to sign and validate JWTs.
- `LLM_API_KEY`: API key for accessing the LLM provider (e.g., Google Gemini).
- `POSTGRES_PASSWORD`: The password for the shared database.

## Secret Injection

In a production environment, secrets should be injected into containers using:
- **Kubernetes Secrets:** Mounted as environment variables or files.
- **Docker Secrets:** For Swarm environments.
- **External Secret Managers:** Fetched at startup by a bootstrap script.
