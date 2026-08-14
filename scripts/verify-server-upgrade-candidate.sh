#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_dir/main/xiaozhi-server"
config_file="$repo_dir/tests/fixtures/isolated-config.yaml"
model_dir="/home/luban/codebase/aiot/xiaozhi-esp32-server/main/xiaozhi-server/models"
image="xiaozhi-server:0.9.6-candidate-20260814"
base_image="xiaozhi-server:server-base-local"
container="xiaozhi-server-v096-smoke-$$"

cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
}
trap cleanup EXIT

test -f "$model_dir/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx"
test -f "$model_dir/SenseVoiceSmall/config.yaml"

if ! git -C "$repo_dir" diff --quiet -- \
  .dockerignore Dockerfile-server-local main/xiaozhi-server || \
  ! git -C "$repo_dir" diff --cached --quiet -- \
    .dockerignore Dockerfile-server-local main/xiaozhi-server; then
  printf 'candidate build inputs must be committed before verification\n' >&2
  exit 1
fi

untracked_inputs="$(git -C "$repo_dir" ls-files --others --exclude-standard -- \
  .dockerignore Dockerfile-server-local main/xiaozhi-server)"
if [[ -n "$untracked_inputs" ]]; then
  printf 'candidate build inputs contain untracked files:\n%s\n' "$untracked_inputs" >&2
  exit 1
fi

source_revision="$(git -C "$repo_dir" log -1 --format=%H -- \
  .dockerignore Dockerfile-server-local main/xiaozhi-server)"
source_tree="$(git -C "$repo_dir" rev-parse HEAD:main/xiaozhi-server)"
dockerfile_blob="$(git -C "$repo_dir" hash-object Dockerfile-server-local)"
dockerignore_blob="$(git -C "$repo_dir" hash-object .dockerignore)"
base_image_id="$(docker image inspect "$base_image" --format '{{.Id}}')"

docker build \
  --file "$repo_dir/Dockerfile-server-local" \
  --tag "$image" \
  --label "org.opencontainers.image.revision=$source_revision" \
  --label "org.opencontainers.image.base.digest=$base_image_id" \
  --label "io.xiaozhi.source-tree=$source_tree" \
  --label "io.xiaozhi.dockerfile=$dockerfile_blob" \
  --label "io.xiaozhi.dockerignore=$dockerignore_blob" \
  "$repo_dir"

docker run --detach \
  --name "$container" \
  --network none \
  --mount "type=bind,src=$config_file,dst=$source_dir/data/.config.yaml,readonly" \
  --mount "type=bind,src=$model_dir,dst=$source_dir/models,readonly" \
  "$image" >/dev/null

for attempt in $(seq 1 45); do
  if ! docker inspect --format '{{.State.Running}}' "$container" 2>/dev/null | grep -qx true; then
    docker logs "$container"
    exit 1
  fi

  if docker exec "$container" python - <<'PY' >/dev/null 2>&1
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:18000/", timeout=2) as response:
    assert response.status == 200
    assert response.read() == b"Server is running\n"
PY
  then
    break
  fi

  if [[ "$attempt" == 45 ]]; then
    docker logs "$container"
    exit 1
  fi
  sleep 1
done

docker exec "$container" python - <<'PY'
import asyncio
import websockets


async def verify():
    async with websockets.connect(
        "ws://127.0.0.1:18000/xiaozhi/v1/",
        open_timeout=3,
        close_timeout=3,
    ) as websocket:
        message = await asyncio.wait_for(websocket.recv(), timeout=3)
        assert "digital-human" in message


asyncio.run(verify())
PY

docker exec "$container" python - <<'PY'
import urllib.request

request = urllib.request.Request(
    "http://127.0.0.1:18003/xiaozhi/ota/",
    data=b"{}",
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=3) as response:
    assert response.status == 200
    body = response.read().decode("utf-8")
    assert "websocket" in body
PY

image_id="$(docker image inspect "$image" --format '{{.Id}}')"
image_revision="$(docker image inspect "$image" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')"
image_base_id="$(docker image inspect "$image" --format '{{index .Config.Labels "org.opencontainers.image.base.digest"}}')"
image_source_tree="$(docker image inspect "$image" --format '{{index .Config.Labels "io.xiaozhi.source-tree"}}')"
image_dockerfile="$(docker image inspect "$image" --format '{{index .Config.Labels "io.xiaozhi.dockerfile"}}')"
image_dockerignore="$(docker image inspect "$image" --format '{{index .Config.Labels "io.xiaozhi.dockerignore"}}')"

test "$image_revision" = "$source_revision"
test "$image_base_id" = "$base_image_id"
test "$image_source_tree" = "$source_tree"
test "$image_dockerfile" = "$dockerfile_blob"
test "$image_dockerignore" = "$dockerignore_blob"

printf 'candidate_image=%s\n' "$image"
printf 'candidate_image_id=%s\n' "$image_id"
printf 'source_revision=%s\n' "$source_revision"
printf 'source_tree=%s\n' "$source_tree"
printf 'dockerfile_blob=%s\n' "$dockerfile_blob"
printf 'dockerignore_blob=%s\n' "$dockerignore_blob"
printf 'base_image=%s\n' "$base_image"
printf 'base_image_id=%s\n' "$base_image_id"
printf 'isolated_network=none\n'
printf 'http_probe=pass\n'
printf 'websocket_probe=pass\n'
printf 'ota_probe=pass\n'
