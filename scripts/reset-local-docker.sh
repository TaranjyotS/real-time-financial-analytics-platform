#!/usr/bin/env bash
set -euo pipefail

docker compose -p rtfa -f infrastructure/docker-compose.yml down -v --remove-orphans

docker rm -f rtfa-postgres rtfa-redis rtfa-zookeeper rtfa-kafka rtfa-backend rtfa-frontend rtfa-prometheus rtfa-grafana 2>/dev/null || true

docker volume rm rtfa_rtfa_postgres_data rtfa_postgres_data 2>/dev/null || true

echo "Local Docker state reset. Now run: docker compose -p rtfa -f infrastructure/docker-compose.yml up --build"
