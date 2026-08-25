.PHONY: help install build build-api build-yolo compose-up compose-down logs ps health ready test-local test-compose lint clean

COMPOSE  ?= docker compose
IMAGE_API ?= fit4110/ai-vision:lab05
IMAGE_YOLO ?= fit4110/ai-yolo:lab05
COMPOSE_PROJECT_NAME ?= smartcampus-vision-lab05

# URL của AI Vision API (trỏ đến container; ngày mai chạy local thì đổi sang localhost:8001)
VISION_API_URL ?= http://localhost:8001

help:
	@echo "Targets:"
	@echo "  install        - npm install (Postman, Newman, Prism, Spectral)"
	@echo "  build          - docker compose build (all services)"
	@echo "  build-api      - build ai-vision image only"
	@echo "  build-yolo     - build ai-yolo image only"
	@echo "  compose-up     - build + run stack (ai-yolo + ai-vision)"
	@echo "  compose-down   - stop and remove stack"
	@echo "  logs           - tail logs of all services"
	@echo "  ps             - list services"
	@echo "  health         - curl /health of all services"
	@echo "  ready          - curl /ready of API (check deps)"
	@echo "  test-compose   - chạy newman trên stack compose"
	@echo "  test-api-url   - chạy tests trỏ đến VISION_API_URL (def: localhost:8001)"
	@echo "  lint           - spectral lint contracts/*.yaml"
	@echo "  clean          - compose down + remove images + reports"

install:
	npm install

build:
	$(COMPOSE) build

build-api:
	$(COMPOSE) build ai-vision

build-yolo:
	$(COMPOSE) build ai-yolo

compose-up:
	$(COMPOSE) up -d --build

compose-down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs -f --tail=100

ps:
	$(COMPOSE) ps

health:
	@echo "--- ai-vision ---";  curl -s http://localhost:8000/health  | python -m json.tool || true
	@echo "--- ai-yolo ---";     curl -s http://localhost:8001/health  | python -m json.tool || true

ready:
	@curl -s http://localhost:8000/ready | python -m json.tool || true

test-compose:
	npm run test:compose

test-api-url:
	@echo "VISION_API_URL=$(VISION_API_URL)"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not reachable"

lint:
	npx @stoplight/spectral-cli lint contracts/*.yaml

clean: compose-down
	docker rmi $(IMAGE_API) $(IMAGE_YOLO) 2>/dev/null || true
	rm -f reports/newman-lab05-*.xml reports/newman-lab05-*.html
	docker volume rm smartcampus-vision-data 2>/dev/null || true
