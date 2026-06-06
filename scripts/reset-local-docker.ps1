docker compose -p rtfa -f infrastructure/docker-compose.yml down -v --remove-orphans
$containers = "rtfa-postgres","rtfa-redis","rtfa-zookeeper","rtfa-kafka","rtfa-backend","rtfa-frontend","rtfa-prometheus","rtfa-grafana"
foreach ($c in $containers) { docker rm -f $c 2>$null }
docker volume rm rtfa_rtfa_postgres_data rtfa_postgres_data 2>$null
Write-Host "Local Docker state reset. Now run: docker compose -p rtfa -f infrastructure/docker-compose.yml up --build"
