#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

python3 - <<'PY'
import base64
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.request


namespace = "cyjdata-prod"

deploy = json.loads(
    subprocess.check_output(
        ["kubectl", "-n", namespace, "get", "deploy", "cyjdata-v2-api", "-o", "json"],
        text=True,
    )
)
available = int(deploy.get("status", {}).get("availableReplicas") or 0)
if available < 1:
    raise SystemExit("cyjdata-v2-api has no available replica")

for configmap in (
    "polarsearch-poc-script",
    "polarsearch-setup-script",
    "polarsearch-validate-script",
):
    subprocess.run(
        ["kubectl", "-n", namespace, "get", "configmap", configmap, "-o", "name"],
        check=True,
        stdout=subprocess.DEVNULL,
    )

secret = json.loads(
    subprocess.check_output(
        ["kubectl", "-n", namespace, "get", "secret", "cyjdata-v2-auth", "-o", "json"],
        text=True,
    )
)
try:
    api_key = base64.b64decode(secret["data"]["api_key"]).decode("utf-8").strip()
except (KeyError, ValueError, UnicodeError) as exc:
    raise SystemExit("cyjdata API key is unavailable") from exc
if len(api_key) < 16:
    raise SystemExit("cyjdata API key is invalid")

tracked = subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0")
needle = api_key.encode("utf-8")
for raw_path in tracked:
    if not raw_path:
        continue
    path = Path(raw_path.decode("utf-8"))
    try:
        if needle in path.read_bytes():
            raise SystemExit("cyjdata API key is present in a tracked file")
    except (OSError, UnicodeError):
        continue


def post(path, payload):
    request = urllib.request.Request(
        "https://data-admin.petsengine.cn" + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": api_key,
            "User-Agent": "xiaozhi-retrieval-contract/1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            if response.status != 200:
                raise SystemExit(f"unexpected HTTP status {response.status}")
            value = json.load(response)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"retrieval contract HTTP status {exc.code}") from exc
    if not isinstance(value, dict):
        raise SystemExit("retrieval contract returned a non-object")
    return value


product = post(
    "/api/v2/internal/ai/search",
    {"query": "猫粮", "types": ["product"], "limit": 3},
)
items = product.get("items")
if product.get("degraded") is not False or not isinstance(items, list) or not items:
    raise SystemExit("production product retrieval is not ready")

knowledge = post(
    "/api/v2/internal/ai/knowledge/search",
    {
        "contractVersion": 1,
        "requestId": "xiaozhi-contract-smoke",
        "query": "幼猫喂养知识",
        "types": ["knowledge", "courseCatalog"],
        "scopes": ["publicKnowledge", "courseCatalog"],
        "allowedEntitlementKeys": [],
        "limit": 3,
        "rerank": True,
    },
)
if knowledge.get("contractVersion") != 1 or not isinstance(
    knowledge.get("items", []), list
):
    raise SystemExit("production knowledge retrieval contract is invalid")

print(
    "production retrieval contract ok: "
    f"product_items={len(items)} "
    f"knowledge_items={len(knowledge.get('items', []))} "
    f"knowledge_degraded={bool(knowledge.get('degraded'))}"
)
PY
