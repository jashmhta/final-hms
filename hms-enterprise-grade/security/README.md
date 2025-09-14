# Security Services

This repository ships optional local dev services for policy and secrets:

- OPA (Open Policy Agent): runs at http://localhost:8181 with default-allow policy at `security/opa/policy.rego`. Services can call `POST /v1/data/hms/allow` with an input document for allow/deny decisions.
- Vault (dev mode): runs at http://localhost:8200 with token `root`. Do not use in production. Intended for local experiments storing secrets and retrieving via HTTP.

Both are wired in docker-compose for local runs. In production, use managed OPA/Vault and mTLS.
