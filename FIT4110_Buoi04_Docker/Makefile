.PHONY: build up down logs ps health test-vision-local test-vision-mock lint clean

# Override images / container names if needed.
COMPOSE ?= docker compose
IMAGE_VISION ?= fit4110/ai-vision:lab04
IMAGE_CORE   ?= fit4110/core-business-mock:lab04
IMAGE_CAMERA ?= fit4110/camera-stream-mock:lab04

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
