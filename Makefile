SHELL := /bin/bash
PWD := $(shell pwd)

default: docker-compose-up

all:

init:
	python3 docker_compose_generator.py
.PHONY: init

docker-image:
	docker build -f ./middleware/Dockerfile -t middleware-base .
	docker build -f ./middleware/rabbitmq/Dockerfile -t rabbitmq-healthy .
	docker build -f ./init/Dockerfile -t "init:latest" .
	docker build -f ./filter/Dockerfile -t "filter-parser:latest" .
	docker build -f ./counter/Dockerfile -t "counter:latest" .
	docker build -f ./reduce_percentage/Dockerfile -t "percentage:latest" .
	docker build -f ./counter_by_date/Dockerfile -t "counter-by-date:latest" .
	docker build -f ./reduce_by_date/Dockerfile -t "total-by-date:latest" .
	docker build -f ./init_regions/Dockerfile -t "init-regions:latest" .
	docker build -f ./distance/Dockerfile -t "distance:latest" .
	docker build -f ./counter_by_region/Dockerfile -t "counter-by-region:latest" .
	docker build -f ./reduce_by_region/Dockerfile -t "total-by-region:latest" .
	docker build -f ./end/Dockerfile -t "end:latest" .
.PHONY: docker-image

docker-compose-up: docker-image
	docker-compose -f docker-compose.yaml up -d --build
.PHONY: docker-compose-up

docker-compose-down:
	docker-compose -f docker-compose.yaml stop -t 1
	docker-compose -f docker-compose.yaml down
.PHONY: docker-compose-down

docker-compose-logs:
	docker-compose -f docker-compose.yaml logs -f
.PHONY: docker-compose-logs
