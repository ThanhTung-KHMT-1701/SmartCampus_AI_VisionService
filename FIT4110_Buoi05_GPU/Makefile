.PHONY: install lint compose-build compose-up compose-ps compose-logs compose-down compose-health test

# Install Node dependencies for Newman/Spectral
install:
	npm install

# Lint OpenAPI contracts
lint:
	npx spectral lint contracts/*.yaml

# Build Docker image
compose-build:
	docker compose build

# Start containers (lần đầu hoặc khi có bản mới)
compose-up:
	docker compose up -d --build

# Kiểm tra trạng thái container
compose-ps:
	docker compose ps

# Theo dõi log
compose-logs:
	docker compose logs -f

# Dừng và xoá container
compose-down:
	docker compose down

# Kiểm tra health tất cả service
compose-health:
	@echo "=== API health ===" && curl -s http://localhost:8000/health && echo "" && \
	@echo "=== AI service health ===" && curl -s http://localhost:9000/health && echo ""

# Chạy Newman test trên stack
test:
	npm run test:compose
