# Security Model

The Golden Corridor Optimization Engine (GCO-Engine) employs a multi-layered security model designed for production environments.

## Layers of Security

1. **Edge Gateway (Public Entrypoint):**
   - The Gateway is the sole public-facing service.
   - It performs initial JWT validation and claim extraction.
   - It routes requests to internal microservices.

2. **Identity & Access Management (IAM):**
   - **SECURITY_MODE:**
     - `dev`: Allows mock tokens (`op_01`, `eng_01`, `admin_01`, `system_01`) for rapid testing.
     - `prod`: Requires valid JWTs signed by a trusted issuer.
   - **Roles:**
     - `Operator`: Can view state, ingest KPIs, and perform shadow writes.
     - `Engineer`: Can perform guarded writes, train policies, and view detailed metrics.
     - `Admin`: Can perform all actions, including configuration changes and rollbacks.
     - `System`: Internal service-to-service communication.

3. **Policy Enforcement Point (OPA):**
   - The Gateway uses Open Policy Agent (OPA) to enforce fine-grained route-level authorization.
   - Policies are defined in Rego and can be updated without redeploying services.

4. **Service-to-Service Security:**
   - Internal services validate JWTs passed by the Gateway.
   - Services use the same `SECURITY_MODE` logic to ensure consistency.

## Environment configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SECURITY_MODE` | `dev` or `prod` | `dev` |
| `GATEWAY_JWT_SECRET` | Secret key for JWT validation | `secret` |
| `JWT_ISSUER` | Expected JWT issuer | `gco-engine` |
| `JWT_AUDIENCE` | Expected JWT audience | `gco-services` |
