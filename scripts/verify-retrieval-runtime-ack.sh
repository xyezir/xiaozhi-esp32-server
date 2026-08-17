#!/usr/bin/env bash
set -euo pipefail

namespace=${RETRIEVAL_ACK_NAMESPACE:-chongyejia-dev}
deployment=${RETRIEVAL_ACK_DEPLOYMENT:-xiaozhi-retrieval-runtime}

kubectl -n "$namespace" rollout status "deployment/$deployment" --timeout=120s
pod=$(kubectl -n "$namespace" get pod \
  -l app.kubernetes.io/name=xiaozhi-retrieval-runtime \
  -o jsonpath='{.items[0].metadata.name}')
test -n "$pod"

kubectl -n "$namespace" exec -i "$pod" -- python - <<'PY'
import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8090/readyz", timeout=3) as response:
    if response.status != 200:
        raise SystemExit("runtime is not ready")
request = urllib.request.Request(
    "http://127.0.0.1:8090/v1/retrieve",
    data=json.dumps(
        {
            "contractVersion": 1,
            "query": "适合幼猫的猫粮",
            "domains": ["product"],
            "limit": 3,
        },
        ensure_ascii=False,
    ).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=8) as response:
    payload = json.load(response)
if not payload.get("answerable") or payload.get("degraded"):
    raise SystemExit("ACK product retrieval smoke failed")
print(
    "ACK retrieval runtime ok: "
    f"items={len(payload.get('items', []))} latency_ms={payload.get('latencyMs')}"
)
PY
