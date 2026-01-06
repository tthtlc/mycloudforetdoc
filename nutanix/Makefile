.PHONY: help install test lint format clean build push deploy logs

REGISTRY ?= myregistry.io/cloudforet
IMAGE_NAME = plugin-nutanix-inven-collector
VERSION ?= 1.0.0
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(VERSION)
NAMESPACE ?= cloudforet

help:
	@echo "Available targets:"
	@echo "  make install        - Install dependencies"
	@echo "  make test          - Run all tests"
	@echo "  make unit-test     - Run unit tests only"
	@echo "  make lint          - Run code linting"
	@echo "  make format        - Format code with black/isort"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make build         - Build Docker image"
	@echo "  make push          - Push Docker image to registry"
	@echo "  make deploy        - Deploy to Kubernetes"
	@echo "  make logs          - Show pod logs"
	@echo "  make restart       - Restart pods"
	@echo "  make help          - Show this help message"

install:
	pip install -r requirements.txt

test:
	pytest src/tests/ -v --tb=short

unit-test:
	pytest src/tests/unit/ -v --tb=short

integration-test:
	pytest src/tests/integration/ -v --tb=short

test-coverage:
	pytest src/tests/ --cov=src/ --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 src/ --max-line-length=120 --count --show-source --statistics
	mypy src/ --ignore-missing-imports

format:
	black src/
	isort src/

format-check:
	black src/ --check
	isort src/ --check-only

clean:
	find src/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find src/ -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/ htmlcov/ .mypy_cache/ dist/ build/ *.egg-info
	docker rmi $(IMAGE) 2>/dev/null || true

build:
	docker build -t $(IMAGE) .
	@echo "Image built: $(IMAGE)"

push:
	docker push $(IMAGE)
	@echo "Image pushed: $(IMAGE)"

deploy:
	helm upgrade --install nutanix-plugin ./charts/plugin-nutanix \
		--namespace $(NAMESPACE) \
		--set image.repository=$(REGISTRY)/$(IMAGE_NAME) \
		--set image.tag=$(VERSION)
	@echo "Deployed to namespace: $(NAMESPACE)"

deploy-dev:
	helm install nutanix-plugin ./charts/plugin-nutanix \
		--namespace $(NAMESPACE) \
		--set replicaCount=1 \
		--set logLevel=DEBUG

delete:
	helm delete nutanix-plugin -n $(NAMESPACE)
	@echo "Deleted from namespace: $(NAMESPACE)"

logs:
	kubectl logs -n $(NAMESPACE) -l app.kubernetes.io/name=plugin-nutanix-inven-collector -f

logs-pod:
	@kubectl logs -n $(NAMESPACE) -l app.kubernetes.io/name=plugin-nutanix-inven-collector --tail=50

restart:
	kubectl rollout restart deployment -n $(NAMESPACE) -l app.kubernetes.io/name=plugin-nutanix-inven-collector

status:
	kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/name=plugin-nutanix-inven-collector
	@echo ""
	helm list -n $(NAMESPACE) | grep nutanix

describe:
	kubectl describe pod -n $(NAMESPACE) -l app.kubernetes.io/name=plugin-nutanix-inven-collector

shell:
	kubectl exec -it -n $(NAMESPACE) \
		$$(kubectl get pod -n $(NAMESPACE) -l app.kubernetes.io/name=plugin-nutanix-inven-collector -o jsonpath='{.items[0].metadata.name}') \
		-- /bin/bash

port-forward:
	kubectl port-forward -n $(NAMESPACE) \
		svc/plugin-nutanix-inven-collector 50051:50051

# CI/CD pipeline
ci: lint test build

# Local development
dev-setup: install format lint test
	@echo "Development environment ready!"

dev-run:
	python src/server.py

# Release
release: clean lint test build push
	@echo "Release $(VERSION) complete!"
	@echo "Image: $(IMAGE)"

# Docker build and test
docker-test:
	docker build --target builder -t $(IMAGE)-test .
	docker run --rm $(IMAGE)-test pytest src/tests/ -v

.PHONY: docker-test
