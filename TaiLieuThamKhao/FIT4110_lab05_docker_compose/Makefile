.PHONY: install lint build run compose-up compose-down logs test-compose

# Install Node dependencies for Prism/Spectral/Newman
install:
	npm install

# Lint OpenAPI contracts with Spectral
lint:
	npx spectral lint contracts/*.yaml

# Build Docker image for API only
build:
	docker build -t fit4110/iot-ingestion:lab05 .

# Run API container standalone (not via compose)
run:
	docker run --rm --name fit4110-api-lab05 -p 8000:8000 --env-file .env.example fit4110/iot-ingestion:lab05

# Compose commands
compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

logs:
	docker compose logs -f

# Run Newman tests on compose stack
test-compose:
	npm run test:compose