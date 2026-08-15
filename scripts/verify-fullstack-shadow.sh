#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
web_image="${XIAOZHI_SHADOW_WEB_IMAGE:-xiaozhi-web:0.9.6-main-20260815-shadow}"
core_image="${XIAOZHI_SHADOW_CORE_IMAGE:-xiaozhi-server:0.9.6-main-20260815-candidate}"
mysql_image="${XIAOZHI_SHADOW_MYSQL_IMAGE:-mysql:9.6.0}"
redis_image="${XIAOZHI_SHADOW_REDIS_IMAGE:-redis:8.0}"
build_proxy="${XIAOZHI_BUILD_PROXY:-http://127.0.0.1:7890}"
model_dir="${XIAOZHI_MODEL_DIR:-/home/luban/codebase/aiot/xiaozhi-esp32-server/main/xiaozhi-server/models}"
vad_model="$model_dir/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx"
config_file="$repo_dir/tests/fixtures/isolated-config.yaml"
suffix="${XIAOZHI_SHADOW_SUFFIX:-$$}"
network="codex-xiaozhi-shadow-$suffix"
db_container="codex-xiaozhi-shadow-db-$suffix"
redis_container="codex-xiaozhi-shadow-redis-$suffix"
web_container="codex-xiaozhi-shadow-web-$suffix"
core_container="codex-xiaozhi-shadow-core-$suffix"
db_alias="shadow-db"
redis_alias="shadow-redis"
web_alias="shadow-web"
db_password="codex-shadow-db-only"

cleanup() {
  docker rm -f \
    "$core_container" \
    "$web_container" \
    "$redis_container" \
    "$db_container" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT

test -f "$vad_model"
test -f "$config_file"
docker image inspect "$core_image" >/dev/null

build_inputs=(
  .dockerignore
  Dockerfile-web
  docs/docker/nginx.conf
  docs/docker/start.sh
  main/manager-api
  main/manager-web
)

if ! git -C "$repo_dir" diff --quiet -- "${build_inputs[@]}" ||
  ! git -C "$repo_dir" diff --cached --quiet -- "${build_inputs[@]}"; then
  printf 'shadow web build inputs must be committed before verification\n' >&2
  exit 1
fi

untracked_inputs="$(git -C "$repo_dir" ls-files --others --exclude-standard -- "${build_inputs[@]}")"
if [[ -n "$untracked_inputs" ]]; then
  printf 'shadow web build inputs contain untracked files\n' >&2
  exit 1
fi

if [[ "${XIAOZHI_SKIP_SHADOW_WEB_BUILD:-0}" != "1" ]]; then
  build_args=(
    --file "$repo_dir/Dockerfile-web"
    --tag "$web_image"
    --label "org.opencontainers.image.revision=$(git -C "$repo_dir" rev-parse HEAD)"
  )
  if [[ -n "$build_proxy" ]]; then
    build_args+=(
      --network host
      --build-arg "HTTP_PROXY=$build_proxy"
      --build-arg "HTTPS_PROXY=$build_proxy"
      --build-arg "NO_PROXY=localhost,127.0.0.1"
    )
  fi
  docker build "${build_args[@]}" "$repo_dir"
else
  docker image inspect "$web_image" >/dev/null
fi

docker network create "$network" >/dev/null

docker run --detach --rm \
  --name "$db_container" \
  --network "$network" \
  --network-alias "$db_alias" \
  --env "MYSQL_ROOT_PASSWORD=$db_password" \
  --env MYSQL_DATABASE=xiaozhi_esp32_server \
  "$mysql_image" >/dev/null

docker run --detach --rm \
  --name "$redis_container" \
  --network "$network" \
  --network-alias "$redis_alias" \
  "$redis_image" >/dev/null

for attempt in $(seq 1 60); do
  if docker exec "$db_container" mysqladmin ping -uroot -p"$db_password" --silent >/dev/null 2>&1 &&
    docker exec "$redis_container" redis-cli ping 2>/dev/null | grep -qx PONG; then
    break
  fi
  if [[ "$attempt" == 60 ]]; then
    printf 'shadow database or Redis did not become ready\n' >&2
    exit 1
  fi
  sleep 1
done

docker run --detach --rm \
  --name "$web_container" \
  --network "$network" \
  --network-alias "$web_alias" \
  --env "SPRING_DATASOURCE_DRUID_URL=jdbc:mysql://$db_alias:3306/xiaozhi_esp32_server?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true" \
  --env SPRING_DATASOURCE_DRUID_USERNAME=root \
  --env "SPRING_DATASOURCE_DRUID_PASSWORD=$db_password" \
  --env "SPRING_DATA_REDIS_HOST=$redis_alias" \
  --env SPRING_DATA_REDIS_PASSWORD= \
  --env SPRING_DATA_REDIS_PORT=6379 \
  "$web_image" >/dev/null

for attempt in $(seq 1 120); do
  if ! docker inspect --format '{{.State.Running}}' "$web_container" 2>/dev/null | grep -qx true; then
    printf 'shadow manager container stopped before readiness\n' >&2
    exit 1
  fi
  if docker exec "$web_container" wget -q -O /dev/null http://127.0.0.1:8002/; then
    break
  fi
  if [[ "$attempt" == 120 ]]; then
    printf 'shadow manager did not become ready\n' >&2
    exit 1
  fi
  sleep 1
done

docker exec "$web_container" wget -q -O /dev/null http://127.0.0.1:8002/xiaozhi/doc.html

migration_count="$(docker exec "$db_container" mysql -N -uroot -p"$db_password" xiaozhi_esp32_server \
  -e "SELECT COUNT(*) FROM DATABASECHANGELOG WHERE ID = '202608151730';" 2>/dev/null)"
provider_field_count="$(docker exec "$db_container" mysql -N -uroot -p"$db_password" xiaozhi_esp32_server \
  -e "SELECT COUNT(*) FROM ai_model_provider WHERE id = 'SYSTEM_TTS_HSDSTTS' AND JSON_SEARCH(fields, 'one', 'api_key') IS NOT NULL;" 2>/dev/null)"
model_config_count="$(docker exec "$db_container" mysql -N -uroot -p"$db_password" xiaozhi_esp32_server \
  -e "SELECT COUNT(*) FROM ai_model_config WHERE id IN ('TTS_HuoshanDoubleStreamTTS', 'TTS_HSDSTTS_V2') AND JSON_UNQUOTE(JSON_EXTRACT(config_json, '$.api_key')) = '';" 2>/dev/null)"
shadow_secret="$(docker exec "$db_container" mysql -N -uroot -p"$db_password" xiaozhi_esp32_server \
  -e "SELECT param_value FROM sys_params WHERE param_code = 'server.secret';" 2>/dev/null)"

test "$migration_count" = "1"
test "$provider_field_count" = "1"
test "$model_config_count" = "2"
test -n "$shadow_secret"
test "$shadow_secret" != "null"

docker run --detach --rm \
  --name "$core_container" \
  --network "$network" \
  --mount "type=bind,src=$config_file,dst=/opt/xiaozhi-esp32-server/data/.config.yaml,readonly" \
  --mount "type=bind,src=$vad_model,dst=/opt/xiaozhi-esp32-server/models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx,readonly" \
  "$core_image" >/dev/null

for attempt in $(seq 1 60); do
  if ! docker inspect --format '{{.State.Running}}' "$core_container" 2>/dev/null | grep -qx true; then
    printf 'shadow core container stopped before readiness\n' >&2
    exit 1
  fi
  if docker exec "$core_container" python - <<'PY' >/dev/null 2>&1
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:18000/", timeout=2) as response:
    assert response.status == 200
PY
  then
    break
  fi
  if [[ "$attempt" == 60 ]]; then
    printf 'shadow core did not become ready\n' >&2
    exit 1
  fi
  sleep 1
done

docker exec \
  --env "SHADOW_MANAGER_SECRET=$shadow_secret" \
  "$core_container" python - <<'PY'
import asyncio
import os

from config.manage_api_client import ManageApiClient, get_server_config


async def verify():
    ManageApiClient(
        {
            "manager-api": {
                "url": "http://shadow-web:8002/xiaozhi/",
                "secret": os.environ["SHADOW_MANAGER_SECRET"],
                "max_retries": 0,
                "timeout": 5,
            }
        }
    )
    config = await get_server_config()
    assert isinstance(config, dict)
    assert "selected_module" in config


asyncio.run(verify())
PY

web_image_id="$(docker image inspect "$web_image" --format '{{.Id}}')"
core_image_id="$(docker image inspect "$core_image" --format '{{.Id}}')"

printf 'shadow_web_image=%s\n' "$web_image"
printf 'shadow_web_image_id=%s\n' "$web_image_id"
printf 'shadow_core_image=%s\n' "$core_image"
printf 'shadow_core_image_id=%s\n' "$core_image_id"
printf 'host_ports=none\n'
printf 'liquibase_migration=pass\n'
printf 'manager_web_probe=pass\n'
printf 'manager_api_probe=pass\n'
printf 'core_probe=pass\n'
printf 'core_to_manager_config=pass\n'
printf 'shadow_cleanup=scheduled\n'
