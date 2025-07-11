echo "show tables = \dt , quit = \q"

docker compose exec db psql -U db-id -d db-name
