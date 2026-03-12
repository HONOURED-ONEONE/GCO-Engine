package pepgw.authz

default allow := false

method := input.request.method
path := input.request.path
claims := input.request.claims
role := claims.role

route_is(path_prefix) { startswith(path, path_prefix) }

allow {
  method == "POST"
  path == "/corridor/approve"
  role == "Admin"
}

allow {
  method == "POST"
  path == "/corridor/propose"
  role == "Engineer"
}

allow {
  method == "POST"
  path == "/corridor/propose"
  role == "Admin"
}

allow {
  route_is("/mode/set")
  role == "Operator"
}

allow {
  route_is("/mode/set")
  role == "Admin"
}

allow {
  route_is("/optimize/")
  role == "Operator"
}

allow {
  route_is("/optimize/")
  role == "Engineer"
}

allow {
  route_is("/optimize/")
  role == "Admin"
}

allow {
  route_is("/llm/proposal/")
  role == "Engineer"
}

allow {
  route_is("/llm/proposal/")
  role == "Admin"
}

allow {
  path == "/llm/evidence/summary"
  role == "Operator"
}

allow {
  path == "/llm/evidence/summary"
  role == "Engineer"
}

allow {
  path == "/llm/evidence/summary"
  role == "Admin"
}

allow {
  claims.scopes[_] == "corridor:approve"
  path == "/corridor/approve"
  method == "POST"
}

# System role can do anything
allow {
  role == "System"
}

# Any authenticated role can do GET reads for demo simplicity
allow {
  method == "GET"
}

opa_output := {
  "allow": allow,
  "headers": {"X-Policy-Version": "v1-stage1"}
}
