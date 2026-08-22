.PHONY: build up down logs ps health test-vision-local test-vision-mock test-wait lint clean wait mock help

# Override images / container names if needed.
COMPOSE ?= docker compose
IMAGE_VISION ?= fit4110/ai-vision:lab04
IMAGE_CORE   ?= fit4110/core-business-mock:lab04
IMAGE_CAMERA ?= fit4110/camera-stream-mock:lab04

help:
	@echo "Common targets:"
	@echo "  make build                # docker compose build"
	@echo "  make up                   # docker compose up -d --build"
	@echo "  make down                 # docker compose down"
	@echo "  make ps                   # docker compose ps"
	@echo "  make logs                 # tail logs"
	@echo "  make health               # curl /health cho 3 service"
	@echo "  make wait                 # bash scripts/wait-for-health.sh localhost 8000"
	@echo "  make mock                 # bash scripts/start-prism-mock.sh"
	@echo "  make test-vision-local    # Newman local (qua container)"
	@echo "  make test-vision-mock     # Newman mock (Prism port 4011)"
	@echo "  make test-wait            # bash scripts/run-newman.sh local (có wait)"
	@echo "  make lint                 # spectral lint contracts/ai-vision.openapi.yaml"
	@echo "  make clean                # down stack + xoá image + reports"

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

ps:
	$(COMPOSE) ps

health:
	curl -s http://localhost:8000/health | python -m json.tool
	@echo "--- core-business-mock ---"
	curl -s http://localhost:4012/health | python -m json.tool
	@echo "--- camera-stream-mock ---"
	curl -s http://localhost:4014/health | python -m json.tool

lint:
	npm run lint:vision

test-vision-mock:
	npm run test:vision:mock

test-vision-local:
	npm run test:vision:local

clean:
	$(COMPOSE) down --remove-orphans
	rm -f reports/newman-vision-local.xml reports/newman-vision-local.html
	docker rmi $(IMAGE_VISION) $(IMAGE_CORE) $(IMAGE_CAMERA) 2>/dev/null || true

# Wait for AI Vision container to become healthy (CI helper).
wait:
	bash scripts/wait-for-health.sh localhost 8000 90

# Run Newman with the same wait helper used by CI.
test-wait:
	bash scripts/wait-for-health.sh localhost 8000 90 \
		&& bash scripts/run-newman.sh local

# Start Prism mock (Lab 03 path) — port 4011.
mock:
	bash scripts/start-prism-mock.sh
