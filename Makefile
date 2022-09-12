include Makefile.env

DOCKER_TAG ?= 0.0.0
DOCKER_USERNAME ?= mohammad-nassar10
DOCKER_PASSWORD ?= 
DOCKER_NAME ?= read-file-module
DOCKER_HOSTNAME ?= ghcr.io
DOCKER_NAMESPACE ?= mohammad-nassar10
DOCKER_CLIENT_NAME ?= read-file-module-client

IMG := ${DOCKER_HOSTNAME}/${DOCKER_NAMESPACE}/${DOCKER_NAME}:${DOCKER_TAG}
CLIENT_IMG := ${DOCKER_HOSTNAME}/${DOCKER_NAMESPACE}/${DOCKER_CLIENT_NAME}:${DOCKER_TAG}

export HELM_EXPERIMENTAL_OCI=1

all: test build

.PHONY: test
test:
	pipenv run python -m unittest discover

.PHONY: build
build:
	pipenv lock -r > requirements.txt
	docker build -f build/Dockerfile . -t ${IMG}
	rm requirements.txt


.PHONY: docker-push
docker-push:
	docker push ${IMG}

.PHONY: build-client
build-client:
	cd helm/client; docker build --tag ${CLIENT_IMG} .

.PHONY: docker-push-client
docker-push-client:
	docker push ${CLIENT_IMG}

.PHONY: push-to-kind
push-to-kind:
	kind load docker-image ${IMG}

include hack/make-rules/helm.mk
include hack/make-rules/tools.mk