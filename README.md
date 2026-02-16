# Pact Contract Testing POC

Proof of Concept für Consumer-Driven Contract Testing mit Pact.

## Architektur

```
┌────────────────┐         ┌─────────────┐         ┌────────────────┐
│    Consumer    │ ──────▶ │ Pact Broker │ ◀────── │    Provider    │
│  (API Client)  │  publish│   (9292)    │  verify │  (FastAPI)     │
└────────────────┘         └─────────────┘         └────────────────┘
```

## Schnellstart

### 1. Infrastruktur starten

```bash
# Broker und Provider starten
docker compose up -d postgres pact-broker provider

# Warten bis alles läuft
docker compose ps
```

### 2. Pact Broker öffnen

- URL: http://localhost:9292
- Username: `pact`
- Password: `pact`

### 3. Consumer Tests ausführen (generiert Pact)

```bash
# Consumer Tests lokal ausführen
docker compose run --rm consumer

# Oder im Container:
docker compose run --rm consumer pytest tests/ -v
```

### 4. Pact zum Broker publishen

```bash
# Pact file zum Broker publishen
docker compose run --rm consumer pact-broker publish ./pacts \
  --broker-base-url=http://pact-broker:9292 \
  --broker-username=pact \
  --broker-password=pact \
  --consumer-app-version=1.0.0
```

### 5. Provider verifizieren

```bash
# Provider Verification ausführen
docker compose run --rm provider pytest tests/ -v
```

## Projektstruktur

```
contract-testing/
├── docker-compose.yml      # Container-Orchestrierung
├── pacts/                  # Generierte Pact-Dateien
├── consumer/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── src/
│   │   └── client.py       # API Client Implementation
│   └── tests/
│       └── test_consumer_contract.py  # Contract Tests
└── provider/
    ├── Dockerfile
    ├── pyproject.toml
    ├── src/
    │   └── main.py         # FastAPI App + Provider States
    └── tests/
        └── test_provider_verification.py
```

## Workflow erklärt

### Consumer-Driven Contract Testing

1. **Consumer definiert Erwartungen**
   - Consumer schreibt Tests die beschreiben, was er von der API braucht
   - Tests laufen gegen einen Mock Server
   - Pact generiert eine JSON-Datei (den "Contract")

2. **Contract wird geteilt**
   - Contract wird zum Pact Broker gepublisht
   - Broker verwaltet alle Contracts und Versionen

3. **Provider verifiziert**
   - Provider lädt Contracts vom Broker
   - Pact spielt die Interaktionen gegen die echte API
   - Provider muss alle Erwartungen erfüllen

### Provider States

Provider States (`given(...)`) erlauben es, den Provider in einen bestimmten Zustand zu versetzen:

```python
pact.given("a user with ID 1 exists")  # State
    .upon_receiving("a request for user 1")
    .with_request("GET", "/users/1")
    ...
```

Der Provider hat einen Endpoint `/_pact/provider-states` der diese States handhabt.

## Lokale Entwicklung

### Consumer Tests lokal (ohne Docker)

```bash
cd consumer
pip install -e ".[test]"
pytest tests/ -v
```

### Provider lokal starten

```bash
cd provider
pip install -e ".[test]"
uvicorn src.main:app --reload
```

## Pact Matchers

Der Consumer Test verwendet flexible Matcher:

| Matcher | Beschreibung | Beispiel |
|---------|--------------|----------|
| `Like(value)` | Typ muss matchen, Wert kann anders sein | `Like(1)` matcht jede Zahl |
| `EachLike(value)` | Array mit mindestens einem Element | `EachLike({"id": 1})` |
| `Term(regex, sample)` | Regex Pattern | `Term(r'\d+', '123')` |

## Nützliche Befehle

```bash
# Alle Container stoppen
docker compose down

# Logs anzeigen
docker compose logs -f provider

# In Container einloggen
docker compose exec provider bash

# Alles neu bauen
docker compose build --no-cache

# Nur Broker + DB starten
docker compose up -d postgres pact-broker
```

## Troubleshooting

### Pact Broker nicht erreichbar
```bash
# Prüfen ob Postgres healthy ist
docker compose ps
docker compose logs postgres
```

### Consumer Tests schlagen fehl
```bash
# Detaillierte Ausgabe
docker compose run --rm consumer pytest tests/ -v --tb=long
```

### Provider Verification schlägt fehl
- Prüfen ob Provider läuft: http://localhost:8000/health
- Provider States korrekt implementiert?
- Pact File vorhanden in `./pacts/`?
