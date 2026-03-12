# Policy / MARL Service

Extracts Policy/MARL logic into a standalone FastAPI microservice that performs safe, governed learning from batch KPIs and generates proposals for corridor or cost shaping — with explicit human approval via governance.

## Key Features
- **Experience Store**: Owns KPI context (corridor version + mode) and drives offline/mini-batch updates.
- **Cost Shaping Proposals**: Suggests small updates to NMPC weights (e.g. shift priority from yield to energy if stable).
- **Uncertainty & Restraint Signals**: Computes uncertainty based on statistical variance/sparsity and sets a restraint flag for downstream NMPC hints.
- **Counterfactual Evaluation**: Hits twin-service to gauge effects of plausible corridor/weight changes before generating a proposal.
- **Safety First**: Zero direct control mutations. Generates proposals for approval via `governance`.

## Endpoints
- `POST /policy/maybe-propose`: main entrypoint (usually from KPI)
- `POST /policy/train`: offline/batch training hook
- `POST /policy/activate/{policy_id}`: set active policy profile
- `GET /policy/active`, `/policy/list`, `/policy/experiences`, `/policy/health`
