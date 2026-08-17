#!/usr/bin/env bash
set -euo pipefail

namespace=${RETRIEVAL_ACK_NAMESPACE:-chongyejia-dev}
deployment=${RETRIEVAL_ACK_DEPLOYMENT:-xiaozhi-retrieval-runtime}
service=${RETRIEVAL_ACK_SERVICE:-xiaozhi-retrieval-runtime}

kubectl -n "$namespace" rollout status "deployment/$deployment" --timeout=120s
test "$(kubectl -n "$namespace" get service "$service" -o jsonpath='{.spec.type}')" = "ClusterIP"
test -z "$(kubectl -n "$namespace" get ingress \
  -l app.kubernetes.io/name=xiaozhi-retrieval-runtime \
  -o name)"

runtime_pod=$(kubectl -n "$namespace" get pod \
  -l app.kubernetes.io/name=xiaozhi-retrieval-runtime \
  --field-selector=status.phase=Running \
  -o jsonpath='{.items[0].metadata.name}')
test -n "$runtime_pod"
kubectl -n "$namespace" exec -i "$runtime_pod" -- python - <<'PY'
import json
import urllib.error
import urllib.request

request = urllib.request.Request(
    "http://127.0.0.1:8090/v1/retrieve",
    data=json.dumps(
        {"contractVersion": 1, "query": "猫粮", "domains": ["product"]}
    ).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    urllib.request.urlopen(request, timeout=3)
except urllib.error.HTTPError as exc:
    if exc.code != 401:
        raise
else:
    raise SystemExit("runtime accepted an unauthenticated retrieval request")
print("ACK retrieval runtime rejects unauthenticated requests")
PY

smoke_image=${RETRIEVAL_ACK_SMOKE_IMAGE:-registry.cn-shanghai.aliyuncs.com/chongyejia/curlimages-curl:latest}

smoke_pod="${deployment}-smoke-$(date +%s)"
cleanup() {
  kubectl -n "$namespace" delete pod "$smoke_pod" --ignore-not-found --wait=false \
    >/dev/null 2>&1 || true
}
trap cleanup EXIT

kubectl -n "$namespace" run "$smoke_pod" \
  --image="$smoke_image" \
  --image-pull-policy=IfNotPresent \
  --restart=Never \
  --labels=app.kubernetes.io/name=xiaozhi-esp32-server \
  --env="RETRIEVAL_SMOKE_URL=http://${service}:8090" \
  --dry-run=client \
  -o json \
  --command -- sh -ec '
curl --fail --silent --show-error --max-time 3 \
  "$RETRIEVAL_SMOKE_URL/readyz" >/dev/null
auth_token=$(cat /run/secrets/retrieval/auth_token)
payload=$(curl --fail --silent --show-error --max-time 10 \
  --header "Content-Type: application/json" \
  --header "X-Retrieval-Token: $auth_token" \
  --data-binary '\''{"contractVersion":1,"query":"适合幼猫的猫粮","domains":["product"],"limit":3}'\'' \
  "$RETRIEVAL_SMOKE_URL/v1/retrieve")
unset auth_token
printf "%s" "$payload" | grep -q '\''"answerable":true'\''
if printf "%s" "$payload" | grep -q '\''"degraded":true'\''; then
  exit 1
fi
product_count=$(printf "%s" "$payload" | grep -o '\''"kind":"product"'\'' | wc -l | tr -d " ")
test "$product_count" -ge 1
printf "ACK retrieval runtime ok: products=%s\\n" "$product_count"
' | python3 -c '
import json
import sys

pod = json.load(sys.stdin)
pod["spec"]["automountServiceAccountToken"] = False
pod["spec"]["securityContext"] = {
    "runAsNonRoot": True,
    "runAsUser": 65532,
    "runAsGroup": 65532,
    "fsGroup": 65532,
    "seccompProfile": {"type": "RuntimeDefault"},
}
pod["spec"]["volumes"] = [
    {
        "name": "retrieval-auth",
        "secret": {
            "secretName": "cyjdata-retrieval-api-key",
            "items": [{"key": "auth_token", "path": "auth_token"}],
            "defaultMode": 288,
        },
    }
]
pod["spec"]["containers"][0]["volumeMounts"] = [
    {
        "name": "retrieval-auth",
        "mountPath": "/run/secrets/retrieval",
        "readOnly": True,
    }
]
json.dump(pod, sys.stdout)
' | kubectl apply -f -

phase=""
for _ in $(seq 1 45); do
  phase=$(kubectl -n "$namespace" get pod "$smoke_pod" \
    -o jsonpath='{.status.phase}' 2>/dev/null || true)
  case "$phase" in
    Succeeded|Failed) break ;;
  esac
  sleep 1
done

kubectl -n "$namespace" logs "$smoke_pod"
test "$phase" = "Succeeded"
