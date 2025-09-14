SHELL := /bin/bash

.PHONY: help generate-keys up down logs bootstrap seed

help:
	@echo "Targets:"
	@echo "  generate-keys    Generate RSA keypair in ./keys for audit encryption"
	@echo "  up               Start docker-compose stack"
	@echo "  down             Stop docker-compose stack"
	@echo "  logs             Tail logs"
	@echo "  seed             Seed demo data (run after up)"
	@echo "  bootstrap        Generate keys and start services"

KEY_DIR := keys
PUB := $(KEY_DIR)/audit_public.pem
PRIV := $(KEY_DIR)/audit_private.pem

$(KEY_DIR):
	mkdir -p $(KEY_DIR)

$(PRIV): | $(KEY_DIR)
	openssl genrsa -out $(PRIV) 2048

$(PUB): $(PRIV)
	openssl rsa -in $(PRIV) -pubout -out $(PUB)

generate-keys: $(PUB)
	@echo "Keys generated at $(KEY_DIR)"

up:
	docker compose up -d

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

seed:
	docker compose exec backend python manage.py migrate --noinput || true
	docker compose exec backend python manage.py seed_demo

bootstrap: generate-keys up
	@echo "Stack started. Grafana at http://localhost:3001, Prometheus at http://localhost:9090"
