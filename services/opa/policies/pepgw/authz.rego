package pepgw.authz

default allow := false

method := input.request.method
path := input.request.path
claims := input.request.claims
role := claims.role

route_is(path_prefix) { startswith(path, path_prefix) }

# Admin only
allow {
  role == "Admin"
}

# System role can do anything
allow {
  role == "System"
}

# Governance
allow {
  method == "POST"
  path == "/corridor/propose"
  role == "Engineer"
}

allow {
  path == "/corridor/version"
  any_authenticated_role
}

allow {
  path == "/corridor/proposals"
  any_authenticated_role
}

allow {
  path == "/corridor/diff"
  role == "Engineer"
}

# Mode
allow {
  route_is("/mode/set")
  role == "Operator"
}

allow {
  path == "/mode/current"
  any_authenticated_role
}

allow {
  path == "/mode/policy"
  any_authenticated_role
}

# Optimizer
allow {
  route_is("/optimize/")
  any_authenticated_role
}

# KPI
allow {
  path == "/kpi/ingest"
  role == "Operator"
}

allow {
  path == "/kpi/recent"
  any_authenticated_role
}

allow {
  path == "/kpi/stats"
  role == "Engineer"
}

# Policy
allow {
  path == "/policy/maybe-propose"
  role == "Operator"
}

allow {
  path == "/policy/maybe-propose"
  role == "Engineer"
}

allow {
  path == "/policy/train"
  role == "Engineer"
}

allow {
  route_is("/policy/activate/")
  role == "Engineer"
}

allow {
  path == "/policy/active"
  any_authenticated_role
}

allow {
  path == "/policy/list"
  any_authenticated_role
}

# Evidence
allow {
  route_is("/evidence/snapshot")
  any_authenticated_role
}

allow {
  route_is("/evidence/files")
  any_authenticated_role
}

allow {
  route_is("/evidence/capture")
  role == "Engineer"
}

allow {
  route_is("/evidence/pack")
  role == "Engineer"
}

# OT
allow {
  route_is("/ot/config")
  role == "Engineer"
}

allow {
  route_is("/ot/arm")
  role == "Operator"
}

allow {
  route_is("/ot/arm")
  role == "Engineer"
}

allow {
  route_is("/ot/disarm")
  any_authenticated_role
}

allow {
  route_is("/ot/shadow/write")
  role == "Operator"
}

allow {
  route_is("/ot/shadow/write")
  role == "Engineer"
}

allow {
  route_is("/ot/guarded/write")
  role == "Engineer"
}

allow {
  route_is("/ot/status")
  any_authenticated_role
}

allow {
  route_is("/ot/alarms")
  any_authenticated_role
}

# LLM
allow {
  route_is("/llm/proposal/")
  role == "Engineer"
}

allow {
  route_is("/llm/evidence/summary")
  any_authenticated_role
}

# Helpers
any_authenticated_role {
  role == "Operator"
}
any_authenticated_role {
  role == "Engineer"
}
any_authenticated_role {
  role == "Admin"
}

opa_output := {
  "allow": allow,
  "headers": {"X-Policy-Version": "v1-prod-hardening"}
}
