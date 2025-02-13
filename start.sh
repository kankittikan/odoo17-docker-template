endpath=$(basename $(pwd))

docker compose down -v
docker compose up -d
docker attach $endpath-web-1