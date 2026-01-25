dev:
	docker compose --env-file deploy/envs/.env.dev \
		-f deploy/docker-compose.yml \
		-f deploy/docker-compose.dev.yml up -d --build

dev-down:
	docker compose -f deploy/docker-compose.yml \
		-f deploy/docker-compose.dev.yml down

prod:
	docker compose --env-file deploy/envs/.env.prod \
		-f deploy/docker-compose.yml \
		-f deploy/docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f deploy/docker-compose.yml \
		-f deploy/docker-compose.prod.yml down
