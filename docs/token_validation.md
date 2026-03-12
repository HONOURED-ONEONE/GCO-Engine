# Token Validation

Token validation is the core mechanism for authentication and authorization in the GCO-Engine.

## JWT Overview

The GCO-Engine uses JSON Web Tokens (JWT) for secure identity propagation across services.

### Token Claims

- `sub`: The subject (user ID).
- `role`: The user's role (`Operator`, `Engineer`, `Admin`, `System`).
- `exp`: Expiration time (standard JWT claim).
- `iss`: Issuer (e.g., `gco-engine`).
- `aud`: Audience (e.g., `gco-services`).

### Validation Logic

1. **Gateway Validation:**
   - The Gateway validates the JWT signature, issuer, and expiration.
   - It also checks for the `aud` claim if enabled.
   - It extracts the `role` and other claims and passes them to internal services via headers or a context object.

2. **Internal Service Validation:**
   - Internal services also perform JWT validation to ensure tokens haven't been tampered with or expired.
   - Services use a shared secret (`GATEWAY_JWT_SECRET`) or public keys (JWKS) to verify signatures.

### Modes of Operation

- **`dev` mode:**
  - Simple mock tokens (e.g., `admin_01`) are accepted.
  - Signature validation is skipped for these specific tokens.
- **`prod` mode:**
  - Strictly requires valid JWTs.
  - All claims (`exp`, `sub`, `role`) must be present and valid.

## Implementation Details

The validation logic is implemented using the `PyJWT` library.

```python
# Simplified Validation Logic
options = {
    "verify_aud": True,
    "verify_iss": SECURITY_MODE == "prod",
    "require": ["exp", "sub", "role"] if SECURITY_MODE == "prod" else []
}

claims = jwt.decode(
    token, 
    GATEWAY_JWT_SECRET, 
    algorithms=["RS256", "HS256"], 
    options=options,
    audience=JWT_AUDIENCE,
    issuer=JWT_ISSUER if SECURITY_MODE == "prod" else None
)
```
