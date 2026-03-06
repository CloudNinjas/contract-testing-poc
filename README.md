# Pact Contract Testing POC

Proof of Concept für Consumer-Driven Contract Testing mit [Pact](https://pact.io) und Python.

## Was ist Contract Testing?

```
Consumer                          Provider
────────                          ────────
"Was BRAUCHE ich?"                "Liefere ich das auch?"
     │                                  │
     ▼                                  ▼
Generiert Vertrag    ─────────▶   Verifiziert Vertrag
(Pact JSON)                       (gegen echte API)
```

**Consumer** = Besteller ("Ich hätte gern...")
**Provider** = Koch ("Ich liefere das Gericht")
**Pact** = Die Speisekarte (der Vertrag zwischen beiden)

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
make up
```

Startet:
- **Pact Broker**: http://localhost:9292 (Login: `pact` / `pact`)
- **Provider API**: http://localhost:8000

### 2. Kompletten Workflow ausführen

```bash
make test
```

Das führt aus:
1. `make consumer-test` → Consumer Tests, generiert Pact JSON
2. `make publish` → Pact zum Broker publishen
3. `make provider-verify` → Provider gegen Pact verifizieren

### 3. Ergebnis im Broker anschauen

Öffne http://localhost:9292 - dort siehst du:
- Den Contract zwischen Consumer und Provider
- Verification Status (✅ oder ❌)
- Versionshistorie

## Konfiguration

Die Konfiguration erfolgt über die `.env` Datei. Kopiere `.env.example` als Vorlage:

```bash
cp .env.example .env
```

### Lokaler Broker vs. PactFlow SaaS

Mit dem `LOCAL` Flag wählst du zwischen lokalem Broker und PactFlow SaaS:

```bash
# .env

# LOCAL=true  → Lokaler Pact Broker (Docker)
# LOCAL=false → PactFlow SaaS

LOCAL=true
```

| Einstellung | `LOCAL=true` | `LOCAL=false` |
|-------------|--------------|---------------|
| Broker | Lokaler Docker Container | PactFlow SaaS |
| `make up` | Startet Postgres + Broker + Provider | Startet nur Provider |
| Auth | Username/Password | Bearer Token |
| URL | `http://localhost:9292` | `https://your-org.pactflow.io` |

### Lokaler Broker (LOCAL=true)

```bash
# .env
LOCAL=true
LOCAL_BROKER_URL=http://pact-broker:9292
LOCAL_BROKER_USERNAME=pact
LOCAL_BROKER_PASSWORD=pact
```

### PactFlow SaaS (LOCAL=false)

```bash
# .env
LOCAL=false
PACTFLOW_BROKER_URL=https://your-org.pactflow.io
PACTFLOW_BROKER_TOKEN=your-api-token-here
```

Den API Token findest du in PactFlow unter: **Settings → API Tokens**

### Aktuellen Modus prüfen

```bash
make help    # Zeigt aktuellen Modus an
make status  # Zeigt Modus + Health-Checks
```

## Alle Make-Befehle

```bash
make help              # Alle Befehle anzeigen (zeigt auch aktuellen Modus)

# Infrastruktur
make up                # Broker + Provider starten (je nach LOCAL Flag)
make down              # Alles stoppen
make clean             # Stoppen + Volumes löschen
make status            # Health-Check aller Services

# Contract Testing - Consumer 1 (UserConsumer)
make consumer-test     # Consumer 1 Tests → generiert Pact
make publish           # Consumer 1 Pact zum Broker publishen
make test              # Consumer 1 Workflow (test + publish + verify)

# Contract Testing - Consumer 2 (OrderConsumer)
make consumer2-test    # Consumer 2 Tests → generiert Pact
make publish2          # Consumer 2 Pact zum Broker publishen
make test2             # Consumer 2 Workflow (test + publish + verify)

# Contract Testing - Alle
make test-all          # Beide Consumer + Provider Verify
make provider-verify   # Provider gegen alle Pacts verifizieren

# Entwicklung
make shell-consumer    # Shell im Consumer 1 Container
make shell-consumer2   # Shell im Consumer 2 Container
make shell-provider    # Shell im Provider Container
make logs              # Logs anzeigen
```

## Projektstruktur

```
contract-testing/
├── consumer/                      # Consumer 1: UserConsumer
│   ├── src/
│   │   └── client.py              # HTTP Client (httpx)
│   ├── tests/
│   │   └── test_consumer_contract.py  # Contract Tests
│   └── scripts/
│       └── publish_pact.py        # Publish-Script
│
├── consumer2/                     # Consumer 2: OrderConsumer
│   ├── src/
│   │   └── client.py              # Order API Client
│   ├── tests/
│   │   └── test_consumer_contract.py  # Contract Tests
│   └── scripts/
│       └── publish_pact.py        # Publish-Script
│
├── provider/                      # Der der die API ANBIETET
│   ├── src/
│   │   └── main.py                # FastAPI App
│   └── tests/
│       └── test_provider_verification.py  # Verification + State Handlers
│
├── pacts/                         # Generierte Contracts (JSON)
├── .env                           # Konfiguration (nicht im Repo)
├── .env.example                   # Vorlage für .env
├── docker-compose.yml
└── Makefile
```

## Wie funktioniert es?

### Consumer Test (test_consumer_contract.py)

```python
from pact import Pact, match

pact = Pact("UserConsumer", "UserProvider")

# Definiere was du erwartest
(
    pact
    .upon_receiving("a request for user 1")
    .given("a user with ID 1 exists")      # State für Provider
    .with_request("GET", "/users/1")
    .will_respond_with(200)
    .with_body({
        "id": match.int(1),                # Typ muss int sein
        "name": match.str("Alice"),        # Typ muss string sein
    })
)

# Test läuft gegen Mock Server
with pact.serve() as mock_server:
    client = UserApiClient(mock_server.url)
    user = client.get_user(1)
    assert user.name == "Alice"

# Am Ende: pact.write_file() → erzeugt JSON
```

### Provider Verification (test_provider_verification.py)

```python
from pact import Verifier

verifier = Verifier("UserProvider")
    .add_transport(url="http://localhost:8080")
    .broker_source(broker_url)
    .state_handler({
        "a user with ID 1 exists": setup_user,  # State Handler
    })

verifier.verify()  # Spielt alle Interactions gegen echte API
```

### State Handler

States bereiten die Datenbank vor:

```python
def setup_user(action, parameters):
    if action == "setup":
        # Daten anlegen
        USERS_DB[1] = {"id": 1, "name": "Alice", ...}
    elif action == "teardown":
        # Aufräumen
        del USERS_DB[1]
```

## Pact Matchers (v3)

| Matcher | Beschreibung | Beispiel |
|---------|--------------|----------|
| `match.int(1)` | Typ muss Integer sein | `"id": match.int(1)` |
| `match.str("x")` | Typ muss String sein | `"name": match.str("Alice")` |
| `match.each_like({})` | Array mit mind. 1 Element | `"users": match.each_like({"id": 1})` |
| `match.regex(r'\d+', "123")` | Regex Pattern | `"code": match.regex(r'\d{3}', "200")` |

## Lokale Entwicklung (ohne Docker)

### Consumer Tests

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

### Provider Verification lokal

```bash
cd provider
pytest tests/ -v
```

## Workflow für Teams

### Als Consumer (API-Nutzer)

1. Schreibe Contract Tests für die Endpoints die du brauchst
2. Führe `make consumer-test` aus → generiert Pact JSON
3. Führe `make publish` aus → pushed zum Broker
4. Teile dem Provider-Team die State-Namen mit

### Als Provider (API-Anbieter)

1. Hole dir Zugang zum Pact Broker
2. Schreibe State Handlers für alle States im Pact
3. Baue Verification in deine CI/CD ein
4. `make provider-verify` published Ergebnis zum Broker

## Troubleshooting

### Broker nicht erreichbar

```bash
make status
docker compose logs pact-broker
```

### State Handler fehlt

```
❌ No state handler found for: "user is admin"
```
→ State Handler im Provider hinzufügen

### Consumer und Provider State matchen nicht

Der State-String muss **exakt** übereinstimmen:
```python
# Consumer
.given("users exist in the system")

# Provider - muss identisch sein!
"users exist in the system": handler_function
```

## Links

- [Pact Documentation](https://docs.pact.io)
- [pact-python GitHub](https://github.com/pact-foundation/pact-python)
- [Pact Broker](https://docs.pact.io/pact_broker)
