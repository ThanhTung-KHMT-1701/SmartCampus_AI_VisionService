.PHONY: install lint mock mock-iot mock-vision mock-all mock-camera-side mock-core-side serve-vision serve-camera-mock serve-core-mock test-mock test-local test-html test-ci test-vision-mock test-vision-local test-vision-data clean

install:
	npm install

lint:
	npm run lint:contracts

mock: mock-iot

mock-iot:
	npm run mock:iot

mock-vision:
	npm run mock:vision

mock-all:
	npm run mock:all

# Side mocks for consumer-side smoke test (Python, cần conda env DichVuKetNoi)
mock-camera-side:
	npm run serve:camera-mock

mock-core-side:
	npm run serve:core-mock

# Host service thật (AI Vision)
serve-vision:
	npm run serve:vision

serve-camera-mock:
	npm run serve:camera-mock

serve-core-mock:
	npm run serve:core-mock

test-mock:
	npm run test:mock

test-local:
	npm run test:local

test-html:
	npm run test:html

test-ci:
	npm run test:ci

# Vision contract tests
test-vision-mock:
	npm run test:vision:mock

test-vision-local:
	npm run test:vision:local

test-vision-data:
	npm run test:vision:data

test-vision-ci:
	npm run lint:vision && npm run test:vision:mock

clean:
	rm -f reports/*.xml reports/*.html reports/*.json prism*.log vision.log
