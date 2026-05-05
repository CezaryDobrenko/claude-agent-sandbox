.PHONY: build start stop logs

port ?= 8000

build:
	@if [ -z "$(name)" ]; then \
		echo "Error: missing image name. Usage: make build name=\"example\""; \
		exit 1; \
	fi

	docker build -t "${name}" .

start:
	@if [ -z "$(image)" ]; then \
		echo "Error: missing image name. Usage: make start image=\"example\""; \
		exit 1; \
	fi

	@if [ -z "$(container)" ]; then \
		echo "Error: missing container name. Usage: make start name=\"example\" container=\"example_container\""; \
		exit 1; \
	fi

	docker run -d --rm \
		--env-file .env \
		-p 8001:8000 \
		--name "$(container)" \
		--mount type=bind,src="./context",dst=/workspace/project \
		"${image}"

stop:
	@if [ -z "$(container)" ]; then \
		echo "Error: missing container name. Usage: make stop container=\"example\""; \
		exit 1; \
	fi
	docker stop "$(container)"

logs:
	@if [ -z "$(container)" ]; then \
		echo "Error: missing container name. Usage: make logs container=\"example\""; \
		exit 1; \
	fi
	docker logs "$(container)"

shell:
	@if [ -z "$(container)" ]; then \
		echo "Error: missing container name. Usage: make shell container=\"example\""; \
		exit 1; \
	fi
	docker exec -it "$(container)" /bin/bash

list:
	docker ps