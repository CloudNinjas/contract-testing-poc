.PHONY: help up down build logs clean \
        consumer-test consumer2-test provider-verify publish publish2 \
        broker provider shell-consumer shell-consumer2 shell-provider \
        test test2 test-all

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
	@echo "Contract Testing (UserConsumer):"
	@echo "  make consumer-test   - Consumer 1 Tests (UserConsumer)"
	@echo "  make publish         - Consumer 1 Pact publishen"
	@echo "  make test            - Consumer 1 Workflow"
	@echo ""
	@echo "Contract Testing (OrderConsumer):"
	@echo "  make consumer2-test  - Consumer 2 Tests (OrderConsumer)"
	@echo "  make publish2        - Consumer 2 Pact publishen"
	@echo "  make test2           - Consumer 2 Workflow"
	@echo ""
	@echo "Contract Testing (Alle):"
	@echo "  make test-all        - Beide Consumer + Provider Verify"
	@echo "  make provider-verify - Provider gegen alle Pacts verifizieren"
	@echo ""
	@echo "Entwicklung:"
	@echo "  make broker          - Nur Broker starten"
	@echo "  make provider        - Nur Provider starten"
	@echo "  make shell-consumer  - Shell im Consumer 1 Container"
	@echo "  make shell-consumer2 - Shell im Consumer 2 Container"
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

# Kompletter Workflow Consumer 1
test: consumer-test publish provider-verify
	@echo ""
	@echo "Consumer 1 Workflow abgeschlossen!"

# =============================================================================
# Consumer 2 (OrderConsumer)
# =============================================================================

# Consumer 2 Tests ausführen - generiert Pact JSON
consumer2-test:
	@echo "Running Consumer 2 (OrderConsumer) Contract Tests..."
	docker compose run --rm consumer2 pytest tests/ -v
	@echo ""
	@echo "Pact file generiert in ./pacts/"

# Consumer 2 Pact zum Broker publishen
publish2:
	@echo "Publishing Consumer 2 Pact (Version: $(CONSUMER_VERSION))..."
	docker compose run --rm \
		-e PACT_BROKER_BASE_URL=http://pact-broker:9292 \
		-e CONSUMER_VERSION=$(CONSUMER_VERSION) \
		consumer2 python scripts/publish_pact.py
	@echo ""
	@echo "Pact published! Check: http://localhost:9292"

# Kompletter Workflow Consumer 2
test2: consumer2-test publish2 provider-verify
	@echo ""
	@echo "Consumer 2 Workflow abgeschlossen!"

# Kompletter Workflow für beide Consumer
test-all: consumer-test consumer2-test publish publish2 provider-verify
	@echo ""
	@echo "Alle Consumer Workflows abgeschlossen!"

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

shell-consumer2:
	docker compose run --rm consumer2 bash

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
