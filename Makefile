.PHONY: help up down build logs clean \
        consumer-test provider-verify publish \
        broker provider shell-consumer shell-provider

# Default target
help:
	@echo "Pact Contract Testing POC"
	@echo ""
	@echo "Infrastruktur:"
	@echo "  make up              - Broker + Provider starten"
	@echo "  make down            - Alles stoppen"
	@echo "  make build           - Images neu bauen"
	@echo "  make logs            - Logs anzeigen"
	@echo "  make clean           - Alles stoppen + Volumes löschen"
	@echo ""
	@echo "Contract Testing:"
	@echo "  make consumer-test   - Consumer Tests ausführen (generiert Pact)"
	@echo "  make publish         - Pact zum Broker publishen"
	@echo "  make provider-verify - Provider gegen Pact verifizieren"
	@echo "  make test            - Kompletter Workflow (test → publish → verify)"
	@echo ""
	@echo "Entwicklung:"
	@echo "  make broker          - Nur Broker starten"
	@echo "  make provider        - Nur Provider starten"
	@echo "  make shell-consumer  - Shell im Consumer Container"
	@echo "  make shell-provider  - Shell im Provider Container"
	@echo ""
	@echo "URLs:"
	@echo "  Pact Broker: http://localhost:9292 (pact/pact)"
	@echo "  Provider:    http://localhost:8000"

# =============================================================================
# Infrastruktur
# =============================================================================

up:
	docker compose up -d postgres pact-broker provider
	@echo ""
	@echo "Warte auf Services..."
	@sleep 3
	@echo "Broker: http://localhost:9292 (pact/pact)"
	@echo "Provider: http://localhost:8000"

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

clean:
	docker compose down -v
	rm -f pacts/*.json

# =============================================================================
# Contract Testing Workflow
# =============================================================================

# Consumer Tests ausführen - generiert Pact JSON
consumer-test:
	@echo "Running Consumer Contract Tests..."
	docker compose run --rm consumer pytest tests/ -v
	@echo ""
	@echo "Pact file generiert in ./pacts/"

# Pact zum Broker publishen
CONSUMER_VERSION ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "1.0.0")
publish:
	@echo "Publishing Pact (Version: $(CONSUMER_VERSION))..."
	docker compose run --rm \
		-e PACT_BROKER_BASE_URL=http://pact-broker:9292 \
		-e CONSUMER_VERSION=$(CONSUMER_VERSION) \
		consumer python scripts/publish_pact.py
	@echo ""
	@echo "Pact published! Check: http://localhost:9292"

# Provider Verification
PROVIDER_VERSION ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "1.0.0")
provider-verify:
	@echo "Verifying Provider against Pact..."
	docker compose run --rm \
		-e PACT_BROKER_BASE_URL=http://pact-broker:9292 \
		-e PROVIDER_VERSION=$(PROVIDER_VERSION) \
		provider pytest tests/ -v -s

# Kompletter Workflow
test: consumer-test publish provider-verify
	@echo ""
	@echo "Contract Testing Workflow abgeschlossen!"

# =============================================================================
# Entwicklung
# =============================================================================

broker:
	docker compose up -d postgres pact-broker
	@echo "Broker: http://localhost:9292"

provider:
	docker compose up -d provider
	@echo "Provider: http://localhost:8000"

shell-consumer:
	docker compose run --rm consumer bash

shell-provider:
	docker compose exec provider bash

# Health checks
status:
	@echo "Container Status:"
	@docker compose ps
	@echo ""
	@echo "Provider Health:"
	@curl -s http://localhost:8000/health 2>/dev/null || echo "Provider nicht erreichbar"
	@echo ""
	@echo "Broker Health:"
	@curl -s -u pact:pact http://localhost:9292/diagnostic/status/heartbeat 2>/dev/null || echo "Broker nicht erreichbar"
