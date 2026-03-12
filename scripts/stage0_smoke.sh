#!/bin/bash

# Simple smoke test against governance endpoints directly.
# Assumes governance is running on port 8001.

echo "Smoke testing Governance Service on http://localhost:8001..."

# 1. Fetch active bounds internally
echo "Testing GET /governance/active..."
RESP=$(curl -s http://localhost:8001/governance/active)
if echo "$RESP" | grep -q "active_version"; then
    echo "✅ /governance/active OK"
else
    echo "❌ /governance/active failed: $RESP"
fi

# 2. Add an audit entry
echo "Testing POST /governance/audit/ingest..."
RESP2=$(curl -s -X POST http://localhost:8001/governance/audit/ingest \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer admin_01" \
    -d '{"event_type": "smoke_test", "data": {"status": "ok"}, "user_id": "admin_01"}')
if echo "$RESP2" | grep -q "recorded"; then
    echo "✅ /governance/audit/ingest OK"
else
    echo "❌ /governance/audit/ingest failed: $RESP2"
fi

# 3. Verify audit chain
echo "Testing GET /governance/audit/verify..."
RESP3=$(curl -s -H "Authorization: Bearer admin_01" http://localhost:8001/governance/audit/verify)
if echo "$RESP3" | grep -q "true"; then
    echo "✅ /governance/audit/verify OK"
else
    echo "❌ /governance/audit/verify failed: $RESP3"
fi

echo "Smoke test complete."
