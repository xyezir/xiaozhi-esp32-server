#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mysql_image=${XIAOZHI_MIGRATION_MYSQL_IMAGE:-mysql:9.6.0}
web_image=${XIAOZHI_MIGRATION_WEB_IMAGE:-xiaozhi-web:dynamic-role-wake-20260817-final2}
suffix=$$
network="xiaozhi-retrieval-migration-$suffix"
db="xiaozhi-retrieval-migration-db-$suffix"
redis="xiaozhi-retrieval-migration-redis-$suffix"
web="xiaozhi-retrieval-migration-web-$suffix"
password="retrieval-migration-test-only"

cleanup() {
  docker rm -f "$web" "$redis" "$db" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker image inspect "$web_image" >/dev/null
docker network create --internal "$network" >/dev/null
docker run -d --rm --name "$db" --network "$network" --network-alias db \
  -e "MYSQL_ROOT_PASSWORD=$password" -e MYSQL_DATABASE=xiaozhi_esp32_server \
  "$mysql_image" >/dev/null
docker run -d --rm --name "$redis" --network "$network" --network-alias redis \
  redis:8.0 >/dev/null

for attempt in $(seq 1 60); do
  if docker exec "$db" mysqladmin ping --protocol=tcp -h127.0.0.1 -uroot \
      -p"$password" --silent >/dev/null 2>&1 && \
    docker exec "$redis" redis-cli ping 2>/dev/null | grep -qx PONG; then
    break
  fi
  [[ "$attempt" != 60 ]] || { echo "disposable dependencies not ready" >&2; exit 1; }
  sleep 1
done

docker run -d --rm --name "$web" --network "$network" \
  -e 'SPRING_DATASOURCE_DRUID_URL=jdbc:mysql://db:3306/xiaozhi_esp32_server?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true' \
  -e SPRING_DATASOURCE_DRUID_USERNAME=root \
  -e "SPRING_DATASOURCE_DRUID_PASSWORD=$password" \
  -e SPRING_DATA_REDIS_HOST=redis \
  -e SPRING_DATA_REDIS_PASSWORD= \
  -e SPRING_DATA_REDIS_PORT=6379 \
  "$web_image" >/dev/null

for attempt in $(seq 1 120); do
  if docker exec "$web" wget -q -O /dev/null http://127.0.0.1:8002/xiaozhi/doc.html 2>/dev/null; then
    break
  fi
  [[ "$attempt" != 120 ]] || { docker logs --tail 80 "$web"; exit 1; }
  sleep 1
done

apply_sql() {
  docker exec -i "$db" mysql -uroot -p"$password" xiaozhi_esp32_server \
    <"$repo_root/main/manager-api/src/main/resources/db/changelog/202608172030.sql" 2>/dev/null
}

apply_sql
apply_sql
count=$(docker exec "$db" mysql -N -uroot -p"$password" xiaozhi_esp32_server \
  -e "SELECT COUNT(*) FROM ai_model_provider WHERE id='SYSTEM_PLUGIN_CYJDATA' AND provider_code='retrieve_from_cyjdata' AND model_type='Plugin' AND JSON_VALID(fields)=1 AND fields NOT LIKE '%api_key%';" 2>/dev/null)
test "$count" = 1

docker exec -i "$db" mysql -uroot -p"$password" xiaozhi_esp32_server \
  <"$repo_root/main/manager-api/src/main/resources/db/changelog/202608172030.rollback.sql" 2>/dev/null
count=$(docker exec "$db" mysql -N -uroot -p"$password" xiaozhi_esp32_server \
  -e "SELECT COUNT(*) FROM ai_model_provider WHERE id='SYSTEM_PLUGIN_CYJDATA';" 2>/dev/null)
test "$count" = 0

apply_sql
printf 'manager retrieval migration ok: idempotent=pass rollback=pass provider=pass\n'
