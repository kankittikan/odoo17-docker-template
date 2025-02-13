endpath=$(basename $(pwd))

docker compose up web -d
docker attach $endpath-web-1