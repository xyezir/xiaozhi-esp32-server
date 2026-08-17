#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

image="xiaozhi-retrieval-runtime:local-$(git rev-parse --short=12 HEAD)"
container="xiaozhi-retrieval-runtime-smoke-$$"
secret_dir=$(mktemp -d)

cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  if [[ -f "$secret_dir/api_key" ]]; then
    chmod u+w "$secret_dir/api_key" 2>/dev/null || true
  fi
  rm -f "$secret_dir/api_key"
  rmdir "$secret_dir" 2>/dev/null || true
}
trap cleanup EXIT

kubectl -n cyjdata-prod get secret cyjdata-v2-auth \
  -o jsonpath='{.data.api_key}' | base64 --decode >"$secret_dir/api_key"
chmod 600 "$secret_dir/api_key"
test -s "$secret_dir/api_key"

docker build --pull=false -f main/retrieval-runtime/Dockerfile -t "$image" .
docker run -d --name "$container" \
  --user "$(id -u):$(id -g)" \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  -e CYJDATA_API_BASE_URL=https://data-admin.petsengine.cn \
  -e CYJDATA_API_KEY_FILE=/run/secrets/cyjdata_api_key \
  -v "$secret_dir/api_key:/run/secrets/cyjdata_api_key:ro" \
  "$image" >/dev/null

for _ in $(seq 1 30); do
  status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container")
  if [[ "$status" == healthy ]]; then
    break
  fi
  if [[ "$status" == unhealthy ]]; then
    docker logs --tail 50 "$container"
    exit 1
  fi
  sleep 1
done
test "$(docker inspect --format '{{.State.Health.Status}}' "$container")" = healthy

docker exec -i "$container" python - <<'PY'
import json
import urllib.request

request = urllib.request.Request(
    "http://127.0.0.1:8090/v1/retrieve",
    data=json.dumps(
        {
            "contractVersion": 1,
            "query": "适合幼猫的猫粮",
            "domains": ["product", "publicKnowledge", "courseCatalog"],
            "limit": 4,
        },
        ensure_ascii=False,
    ).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=8) as response:
    payload = json.load(response)
if payload.get("contractVersion") != 1:
    raise SystemExit("invalid runtime contract version")
if not payload.get("answerable") or not any(
    item.get("kind") == "product" for item in payload.get("items", [])
):
    raise SystemExit("runtime product retrieval is not answerable")
if any("restricted" in str(item).lower() for item in payload.get("items", [])):
    raise SystemExit("restricted content escaped the public runtime")
print(
    "local retrieval runtime ok: "
    f"items={len(payload.get('items', []))} "
    f"latency_ms={payload.get('latencyMs')} "
    f"degraded={bool(payload.get('degraded'))}"
)
PY

if docker port "$container" | grep -q .; then
  echo "runtime unexpectedly publishes a host port" >&2
  exit 1
fi
