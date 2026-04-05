# BRaaS Architecture Documentation

## System Overview

BRaaS (Bio Research-as-a-Service) is a full AI-based automated pipeline for biological research experiments. The system orchestrates the complete lifecycle of experiments from natural language request intake through execution, data collection, and analysis.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BRaaS AI Pipeline Architecture                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   STAGE 1    │    │   STAGE 2    │    │   STAGE 3    │    │   STAGE 4    │   │
│  │   INTAKE     │───▶│   PARSING    │───▶│  PROTOCOL    │───▶│  SCHEDULING  │   │
│  │  NLP Engine  │    │   & ENTITY   │    │  GENERATION  │    │  AI Scheduler│   │
│  │              │    │  EXTRACTION  │    │   Protocol   │    │              │   │
│  │  User Input  │    │              │    │   Generator  │    │  Equipment   │   │
│  │  Request     │    │  Experiment  │    │              │    │  Resources   │   │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘   │
│         │                  │                   │                   │             │
│         ▼                  ▼                   ▼                   ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   STAGE 5    │    │   STAGE 6    │    │   STAGE 7    │    │   STAGE 8    │   │
│  │  VALIDATION  │───▶│  EXECUTION   │───▶│    DATA      │───▶│  ANALYSIS    │   │
│  │   Protocol   │    │   ROBOTICS   │    │  COLLECTION  │    │   Engine     │   │
│  │   Checker    │    │  Controller  │    │   Plate     │    │              │   │
│  │              │    │              │    │   Reader     │    │  Statistical │   │
│  │  Compliance  │    │  Lab Robot   │    │  Instrument  │    │  Processing  │   │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘   │
│         │                  │                   │                   │             │
│         ▼                  ▼                   ▼                   ▼             │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │                           STAGE 9-10 (OUTPUT)                                 │ │
│  │   REPORT GENERATION   │   RESULT STORAGE   │   NOTIFICATION                  │ │
│  │   Data Visualization   │   Neo4j Graph DB   │   MQTT Pub/Sub                  │ │
│  │   PDF/PPT Reports     │   File Storage     │   Webhook Alerts                │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Pipeline Stages

### Stage 1: Natural Language Intake (NLP Engine)

**Purpose:** Parse and interpret natural language experiment requests from users.

**Input:** Raw text requests (e.g., "run an ELISA for IL-6 in 48 mouse serum samples")

**Output:** Structured experiment definition containing:
- Experiment type (ELISA, qPCR, Cell Culture, Western Blot, etc.)
- Target molecule (protein, gene, metabolite)
- Sample type and organism
- Sample count and metadata

**Key Components:**
- `NLPIntakeEngine`: Main natural language processing engine
- Entity extractor for proteins, genes, organisms
- Intent classifier for experiment types
- Semantic parser for parameter extraction

**AI Models Used:**
- Large Language Model (GPT-4/Claude) for semantic understanding
- Named Entity Recognition (NER) for biological entities
- Custom intent classification model

---

### Stage 2: Parsing and Entity Extraction

**Purpose:** Extract and validate biological entities and parameters from parsed requests.

**Input:** Raw text from Stage 1

**Output:**
- Extracted entities (proteins, genes, cell lines, organisms)
- Sample metadata (type, count, preparation requirements)
- Parameter specifications (concentrations, volumes, temperatures)

**Key Components:**
- `EntityExtractor`: Biological entity recognition
- `ParameterParser`: Numerical and categorical parameter extraction
- `OntologyMapper`: Mapping to standard biological ontologies (GO, UniProt, MGED)

**AI Models Used:**
- Transformer-based NER (BioBERT, SciBERT)
- Custom entity linking to knowledge graphs

---

### Stage 3: Protocol Generation

**Purpose:** Generate detailed, executable experimental protocols from structured definitions.

**Input:** Structured experiment definition from Stages 1-2

**Output:** Complete experimental protocol containing:
- Step-by-step instructions
- Reagent specifications and quantities
- Equipment settings and parameters
- Timing and incubation conditions
- Safety notes and quality control checkpoints

**Key Components:**
- `ProtocolGenerator`: Main protocol generation engine
- `ParameterOptimizer`: Optimize protocol parameters based on context
- `ReagentCalculator`: Calculate reagent volumes and concentrations
- `SafetyChecker`: Identify potential safety issues

**AI Models Used:**
- LLM fine-tuned on protocol literature
- Reinforcement learning for parameter optimization
- Knowledge graph reasoning for reagent compatibility

---

### Stage 4: AI Scheduling

**Purpose:** Optimize experiment scheduling and resource allocation across laboratory equipment.

**Input:** Generated protocol with resource requirements

**Output:**
- Optimized execution schedule
- Equipment assignments
- Conflict-free time slots
- Priority-based queue management

**Key Components:**
- `AIScheduler`: Main scheduling engine
- `ResourceAllocator`: Equipment and reagent allocation
- `ConflictDetector`: Scheduling conflict detection and resolution
- `PriorityQueue`: Multi-level priority queue management

**AI Models Used:**
- Constraint satisfaction solvers
- Genetic algorithms for multi-objective optimization
- Graph neural networks for resource dependency modeling

---

### Stage 5: Protocol Validation

**Purpose:** Validate generated protocols for safety, compliance, and feasibility.

**Input:** Generated protocol from Stage 3

**Output:**
- Validation report with warnings/errors
- Compliance checklist
- Feasibility assessment
- Required corrections if any

**Key Components:**
- `ProtocolValidator`: Main validation engine
- `SafetyChecker`: Safety protocol compliance
- `RegulatoryChecker`: GDPR/ethics compliance
- `FeasibilityAnalyzer`: Resource and capability checking

**AI Models Used:**
- Rule-based validation engines
- LLM for complex scenario analysis

---

### Stage 6: Robot Execution Control

**Purpose:** Execute validated protocols using robotic laboratory equipment.

**Input:** Validated protocol with execution instructions

**Output:**
- Execution status and progress
- Robot instruction set
- Real-time instrument feedback
- Error detection and recovery

**Key Components:**
- `RobotController`: Main robot orchestration
- `MotionPlanner`: Robot arm path planning
- `InstrumentInterface`: Communication with lab instruments
- `ErrorHandler`: Exception handling and recovery

**AI Models Used:**
- Robot motion planning algorithms
- Computer vision for object detection
- Reinforcement learning for adaptive execution

---

### Stage 7: Data Collection (Instrument Integration)

**Purpose:** Collect experimental data from laboratory instruments.

**Input:** Running experiment with instrument connections

**Output:**
- Raw instrument data (plate reader, qPCR cycler, etc.)
- Time-series measurements
- Quality metrics and flags
- Data provenance tracking

**Key Components:**
- `InstrumentController`: Multi-instrument coordination
- `DataCollector`: Real-time data acquisition
- `PlateReaderInterface`: Microplate reader communication
- `QPCRInterface`: qPCR cycler data extraction

**AI Models Used:**
- Signal processing for noise reduction
- Anomaly detection for quality control

---

### Stage 8: Data Analysis Engine

**Purpose:** Process, analyze, and interpret experimental data.

**Input:** Raw data from Stage 7

**Output:**
- Processed data with quality control
- Concentration calculations
- Statistical analysis results
- Curve fitting parameters

**Key Components:**
- `DataAnalysisEngine`: Main analysis orchestrator
- `CurveFitter`: 4PL/5PL curve fitting for ELISAs
- `StatisticalAnalyzer`: Hypothesis testing, ANOVA, t-tests
- `OutlierDetector`: Statistical outlier identification
- `Normalizer`: Data normalization routines

**AI Models Used:**
- SciPy/NumPy for numerical computation
- scikit-learn for machine learning-based analysis
- Custom statistical models for bioassays

---

### Stage 9: Report Generation

**Purpose:** Generate comprehensive reports and visualizations.

**Input:** Analysis results from Stage 8

**Output:**
- PDF reports with figures
- PowerPoint presentations
- Interactive data visualizations
- Exportable data tables

**Key Components:**
- `ReportGenerator`: Main report orchestration
- `FigureGenerator`: Matplotlib/Seaborn visualizations
- `PDFBuilder`: ReportLab PDF generation
- `PPTXBuilder`: python-pptx presentation creation

**AI Models Used:**
- Automated figure generation
- Natural language summary generation

---

### Stage 10: Result Storage and Notification

**Purpose:** Store results and notify relevant stakeholders.

**Input:** Complete experiment results

**Output:**
- Graph database storage (Neo4j)
- File storage for raw data
- MQTT notifications
- Webhook alerts
- API results response

**Key Components:**
- `ResultStorage`: Multi-backend storage management
- `Neo4jConnector`: Graph database operations
- `NotificationService`: MQTT pub/sub notifications
- `WebhookManager`: External system notifications

**AI Models Used:**
- Knowledge graph embedding for result relationships
- Automated tagging and categorization

---

## Data Flow Diagram

```
User Request
     │
     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         External Systems Integration                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   REST API ─────▶ FastAPI Server ─────▶ PipelineOrchestrator                 │
│        │                                    │                                   │
│   WebSocket ────▶ WebSocket Handler ────▶ Real-time Updates                  │
│                                                                                │
│   MQTT Broker ──▶ Message Subscriber ───▶ NotificationService                │
│                                                                                │
└──────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Knowledge Graph (Neo4j)                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   Nodes:           │    Relationships:                                        │
│   - Experiments    │    - USES_PROTOCOL                                       │
│   - Protocols      │    - RUNS_ON_EQUIPMENT                                   │
│   - Samples        │    - GENERATES_DATA                                      │
│   - Results        │    - DERIVED_FROM                                         │
│   - Equipment      │    - CONTAINS_ENTITY                                     │
│   - Reagents       │                                                          │
│                                                                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

## API Reference Summary

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/experiments` | Submit new experiment request |
| GET | `/api/v1/experiments/{id}` | Get experiment status and results |
| GET | `/api/v1/experiments` | List all experiments |
| DELETE | `/api/v1/experiments/{id}` | Cancel experiment |
| POST | `/api/v1/experiments/{id}/retry` | Retry failed experiment |

### Protocol Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/protocols/generate` | Generate new protocol |
| GET | `/api/v1/protocols/{id}` | Get protocol details |
| PUT | `/api/v1/protocols/{id}` | Update protocol |
| POST | `/api/v1/protocols/{id}/validate` | Validate protocol |

### Analysis Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analysis/elisa` | Analyze ELISA data |
| POST | `/api/v1/analysis/qpcr` | Analyze qPCR data |
| POST | `/api/v1/analysis/curve-fit` | Perform curve fitting |
| POST | `/api/v1/analysis/statistics` | Run statistical analysis |

### Scheduler Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/schedule/slots` | Get available time slots |
| POST | `/api/v1/schedule/reserve` | Reserve equipment slot |
| GET | `/api/v1/equipment` | List all equipment |
| GET | `/api/v1/equipment/{id}/utilization` | Get equipment utilization |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `ws://host:port/ws/experiments/{id}` | Real-time experiment progress |
| `ws://host:port/ws/equipment/{id}` | Equipment status updates |

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BRAAS_ENV` | `development` | Environment (development/staging/production) |
| `BRAAS_LOG_LEVEL` | `INFO` | Logging level |
| `BRAAS_DB_URL` | `neo4j://localhost:7687` | Neo4j database URL |
| `BRAAS_DB_USER` | `neo4j` | Neo4j username |
| `BRAAS_DB_PASSWORD` | - | Neo4j password (required) |
| `BRAAS_MQTT_URL` | `mqtt://localhost:1883` | MQTT broker URL |
| `BRAAS_REDIS_URL` | `redis://localhost:6379` | Redis URL for caching |
| `BRAAS_API_HOST` | `0.0.0.0` | API server host |
| `BRAAS_API_PORT` | `8000` | API server port |
| `BRAAS_OPENAI_API_KEY` | - | OpenAI API key for LLM |
| `BRAAS_ANTHROPIC_API_KEY` | - | Anthropic API key for LLM |
| `BRAAS_LLM_MODEL` | `gpt-4` | Default LLM model |
| `BRAAS_INSTRUMENT_TIMEOUT` | `300` | Instrument communication timeout (seconds) |
| `BRAAS_MAX_CONCURRENT_EXPERIMENTS` | `10` | Maximum concurrent experiments |

### Configuration File (braas/config.py)

```python
class Settings(BaseSettings):
    """BRaaS Application Settings"""

    # Application
    app_name: str = "BRaaS"
    app_version: str = "0.1.0"
    environment: str = "development"

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]

    # Database
    database_url: str = "neo4j://localhost:7687"
    database_user: str = "neo4j"
    database_password: str = ""

    # Cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 3600

    # LLM Services
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000

    # MQTT
    mqtt_url: str = "mqtt://localhost:1883"
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topics: list[str] = ["braas/experiments", "braas/equipment"]

    # Scheduling
    max_concurrent_experiments: int = 10
    default_experiment_timeout: int = 7200
    scheduling_horizon_days: int = 7

    # Analysis
    outlier_detection_threshold: float = 3.0
    curve_fit_r_squared_threshold: float = 0.95

    # File Storage
    output_directory: Path = Path("outputs")
    max_file_size_mb: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = False
```

## Deployment Guide

### Prerequisites

- Python 3.11+
- Neo4j 4.4+ (or Neo4j Aura for cloud)
- Redis 6+ (for caching and pub/sub)
- MQTT Broker (Mosquitto recommended)
- Docker (optional, for containerized deployment)

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/braas-ai-pipeline.git
cd braas-ai-pipeline
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Start Neo4j and Redis:
```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 neo4j:4.4
docker run -d --name redis -p 6379:6379 redis:6
```

6. Run the API server:
```bash
python scripts/run_api.py --host 0.0.0.0 --port 8000
```

7. Run the pipeline CLI (in another terminal):
```bash
python scripts/run_pipeline.py "run an ELISA for IL-6 in 48 mouse serum samples"
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t braas:latest .
```

2. Run with Docker Compose:
```yaml
version: '3.8'
services:
  braas:
    image: braas:latest
    ports:
      - "8000:8000"
    environment:
      - BRAAS_DB_URL=neo4j://neo4j:7687
      - BRAAS_REDIS_URL=redis://redis:6379
      - BRAAS_MQTT_URL=mqtt://mosquitto:1883
    depends_on:
      - neo4j
      - redis
      - mosquitto

  neo4j:
    image: neo4j:4.4
    ports:
      - "7474:7474"
      - "7687:7687"

  redis:
    image: redis:6
    ports:
      - "6379:6379"

  mosquitto:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
```

```bash
docker-compose up -d
```

### Kubernetes Deployment

Helm charts are available in the `deploy/helm` directory:

```bash
helm install braas ./deploy/helm \
  --set neo4j.enabled=true \
  --set redis.enabled=true \
  --set mqtt.enabled=true \
  --set api_key=your-openai-api-key
```

### Monitoring and Observability

BRaaS integrates with Prometheus for metrics collection:

- Metrics endpoint: `/metrics`
- Key metrics:
  - `braas_experiments_total`: Total experiments run
  - `braas_experiment_duration_seconds`: Experiment execution time
  - `braas_pipeline_stage_duration_seconds`: Time spent in each stage
  - `braas_equipment_utilization`: Equipment utilization percentage

Structured logging with structlog:
```python
import structlog
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)
```

### Security Considerations

1. API authentication via JWT tokens
2. Role-based access control (RBAC)
3. API key rotation for LLM services
4. Encrypted communication (TLS)
5. Input sanitization for experiment requests
6. Rate limiting on API endpoints

### Backup and Recovery

1. Neo4j backup:
```bash
neo4j-admin backup --backup-dir=/path/to/backup --database=neo4j
```

2. Regular exports of experiment data via API:
```bash
curl -X GET http://localhost:8000/api/v1/experiments/export > experiments.json
```

---

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/braas-ai-pipeline/issues
- Documentation: https://braas.readthedocs.io/
