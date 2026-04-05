# BRaaS - Bio Research-as-a-Service AI Pipeline

[![CI](https://github.com/your-org/braas-ai-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/braas-ai-pipeline/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**BRaaS** is a full AI-based automated pipeline for biological research experiments. Transform natural language experiment requests into executed protocols with integrated robotics, instrument control, and comprehensive data analysis.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           BRaaS 10-Stage AI Pipeline                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │    STAGE    │    │    STAGE    │    │    STAGE    │    │    STAGE    │            │
│  │      1      │───▶│      2      │───▶│      3      │───▶│      4      │            │
│  │   NATURAL   │    │   PARSING   │    │  PROTOCOL   │    │     AI      │            │
│  │   LANGUAGE  │    │    & ENTITY │    │ GENERATION  │    │ SCHEDULING  │            │
│  │   INTAKE    │    │  EXTRACTION │    │             │    │             │            │
│  │  NLP Engine │    │             │    │   Protocol  │    │  Equipment  │            │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘            │
│         │                  │                   │                   │                  │
│         ▼                  ▼                   ▼                   ▼                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │    STAGE    │    │    STAGE    │    │    STAGE    │    │    STAGE    │            │
│  │      5      │───▶│      6      │───▶│      7      │───▶│      8      │            │
│  │ VALIDATION  │    │  EXECUTION  │    │    DATA     │    │   DATA      │            │
│  │             │    │   ROBOTICS  │    │  COLLECTION │    │  ANALYSIS   │            │
│  │   Protocol  │    │  Controller │    │  Instrument │    │   Engine    │            │
│  │   Checker   │    │             │    │  Interface  │    │             │            │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘            │
│         │                  │                   │                   │                  │
│         ▼                  ▼                   ▼                   ▼                  │
│  ┌────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              STAGES 9-10                                      │   │
│  │    REPORT GENERATION    │    RESULT STORAGE    │    NOTIFICATIONS           │   │
│  │    PDF/PPT Reports      │    Neo4j Graph DB     │    MQTT/Webhooks           │   │
│  │    Data Visualization    │    File Storage      │    Real-time Alerts        │   │
│  └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Natural Language Interface**: Submit experiment requests in plain English
- **AI-Powered Protocol Generation**: Automatically generate detailed experimental protocols
- **Multi-Experiment Support**: ELISA, qPCR, Cell Culture, Western Blot, and more
- **Intelligent Scheduling**: AI-optimized equipment allocation and conflict resolution
- **Robotic Integration**: Direct control of laboratory robots and automated systems
- **Instrument Control**: Unified interface for plate readers, qPCR cyclers, and more
- **Advanced Data Analysis**: 4PL/5PL curve fitting, statistical analysis, outlier detection
- **Real-time Monitoring**: WebSocket-based experiment tracking and status updates
- **Knowledge Graph**: Neo4j-backed experiment provenance and relationship tracking
- **Comprehensive Reporting**: Automated PDF and PowerPoint report generation
- **MQTT Notifications**: Pub/sub integration for laboratory automation systems
- **RESTful API**: Full API access for integration with LIMS and other systems
- **Structured Logging**: structlog integration for observability
- **Prometheus Metrics**: Built-in metrics for monitoring and alerting
- **Containerized Deployment**: Docker and Kubernetes support
- **Extensible Architecture**: Modular design for easy extension
- **Type Safety**: Full Pydantic models and type hints throughout
- **Async/Await**: Fully asynchronous implementation for high throughput
- **Testing Suite**: Comprehensive unit and integration test coverage
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment

## Installation

### Requirements

- Python 3.11 or higher
- Neo4j 4.4+ (or Neo4j Aura for cloud deployment)
- Redis 6+ (for caching and pub/sub)
- MQTT Broker (Mosquitto recommended)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/your-org/braas-ai-pipeline.git
cd braas-ai-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Run the API server
python scripts/run_api.py --host 0.0.0.0 --port 8000
```

### Docker Installation

```bash
# Build the Docker image
docker build -t braas:latest .

# Run with Docker Compose
docker-compose up -d
```

## Quick Start

### Running the Pipeline via CLI

Execute experiments directly from the command line:

```bash
# Run an ELISA experiment
python scripts/run_pipeline.py "run an ELISA for IL-6 in 48 mouse serum samples" --output-dir outputs/

# Run a qPCR experiment
python scripts/run_pipeline.py "perform qPCR for GAPDH gene expression in human blood" --output-dir outputs/

# Run with custom output directory
python scripts/run_pipeline.py "culture HEK293 cells in DMEM medium" --output-dir ./experiment_results/
```

### Starting the API Server

Start the FastAPI server for REST API access:

```bash
# Basic usage
python scripts/run_api.py --host 0.0.0.0 --port 8000

# Development mode with auto-reload
python scripts/run_api.py --host 0.0.0.0 --port 8000 --reload

# Production with multiple workers
python scripts/run_api.py --host 0.0.0.0 --port 8000 --workers 4
```

### API Examples

```bash
# Submit an experiment
curl -X POST http://localhost:8000/api/v1/experiments \
  -H "Content-Type: application/json" \
  -d '{"request": "run an ELISA for IL-6 in human serum samples"}'

# Get experiment status
curl http://localhost:8000/api/v1/experiments/exp_001

# List all experiments
curl http://localhost:8000/api/v1/experiments

# Analyze ELISA data
curl -X POST http://localhost:8000/api/v1/analysis/elisa \
  -H "Content-Type: application/json" \
  -d @elisa_data.json
```

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           BRaaS Architecture             │
                    └─────────────────────────────────────────┘

  User Request ──▶ [NLP Engine] ──▶ [Protocol Generator] ──▶ [Scheduler]
                         │                   │                      │
                         ▼                   ▼                      ▼
                   [Entity Extract]    [Parameter Optim]    [Equipment Alloc]
                         │                   │                      │
                         ▼                   ▼                      ▼
                   [Validation] ───▶ [Robot Controller] ───▶ [Instrument Ctrl]
                                             │                      │
                                             ▼                      ▼
                                     [Data Collector] ───▶ [Analysis Engine]
                                                              │
                                                              ▼
                                                       [Report Generator]
                                                              │
                                                              ▼
                               [Neo4j Graph DB] ◀──▶ [Notification Service]
```

### Pipeline Stages

| Stage | Name | Description |
|-------|------|-------------|
| 1 | Natural Language Intake | Parse user requests using LLM |
| 2 | Parsing & Entity Extraction | Extract proteins, genes, organisms |
| 3 | Protocol Generation | Generate detailed experimental protocols |
| 4 | AI Scheduling | Optimize equipment allocation |
| 5 | Protocol Validation | Validate safety and feasibility |
| 6 | Robot Execution | Execute protocols via lab robotics |
| 7 | Data Collection | Collect data from instruments |
| 8 | Data Analysis | Process data, curve fitting, statistics |
| 9 | Report Generation | Create PDF/PPT reports |
| 10 | Result Storage | Store in Neo4j, send notifications |

## API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/experiments` | Submit new experiment request |
| `GET` | `/api/v1/experiments/{id}` | Get experiment status and results |
| `GET` | `/api/v1/experiments` | List all experiments |
| `DELETE` | `/api/v1/experiments/{id}` | Cancel experiment |
| `POST` | `/api/v1/experiments/{id}/retry` | Retry failed experiment |

### Protocol Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/protocols/generate` | Generate new protocol |
| `GET` | `/api/v1/protocols/{id}` | Get protocol details |
| `PUT` | `/api/v1/protocols/{id}` | Update protocol |
| `POST` | `/api/v1/protocols/{id}/validate` | Validate protocol |

### Analysis Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analysis/elisa` | Analyze ELISA data |
| `POST` | `/api/v1/analysis/qpcr` | Analyze qPCR data |
| `POST` | `/api/v1/analysis/curve-fit` | Perform curve fitting |
| `POST` | `/api/v1/analysis/statistics` | Run statistical analysis |

### Equipment & Scheduling

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/schedule/slots` | Get available time slots |
| `POST` | `/api/v1/schedule/reserve` | Reserve equipment slot |
| `GET` | `/api/v1/equipment` | List all equipment |
| `GET` | `/api/v1/equipment/{id}/utilization` | Get equipment utilization |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `ws://host:port/ws/experiments/{id}` | Real-time experiment progress |
| `ws://host:port/ws/equipment/{id}` | Equipment status updates |

### Health & Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check |
| `GET` | `/metrics` | Prometheus metrics |

## Configuration

BRaaS is configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BRAAS_ENV` | `development` | Environment mode |
| `BRAAS_LOG_LEVEL` | `INFO` | Logging level |
| `BRAAS_DB_URL` | `neo4j://localhost:7687` | Neo4j database URL |
| `BRAAS_DB_USER` | `neo4j` | Neo4j username |
| `BRAAS_DB_PASSWORD` | - | Neo4j password (required) |
| `BRAAS_MQTT_URL` | `mqtt://localhost:1883` | MQTT broker URL |
| `BRAAS_REDIS_URL` | `redis://localhost:6379` | Redis URL |
| `BRAAS_API_HOST` | `0.0.0.0` | API server host |
| `BRAAS_API_PORT` | `8000` | API server port |
| `BRAAS_OPENAI_API_KEY` | - | OpenAI API key |
| `BRAAS_ANTHROPIC_API_KEY` | - | Anthropic API key |
| `BRAAS_LLM_MODEL` | `gpt-4` | Default LLM model |

Create a `.env` file:

```bash
BRAAS_ENV=development
BRAAS_DB_URL=neo4j://localhost:7687
BRAAS_DB_USER=neo4j
BRAAS_DB_PASSWORD=your-neo4j-password
BRAAS_OPENAI_API_KEY=sk-your-openai-key
BRAAS_ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
BRAAS_LLM_MODEL=gpt-4
```

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository** and create your branch from `main`
2. **Install development dependencies**: `pip install -r requirements.txt`
3. **Run tests**: `pytest`
4. **Run linters**:
   ```bash
   black .
   isort .
   mypy .
   ruff check .
   ```
5. **Commit your changes** with clear, descriptive messages
6. **Submit a pull request** with a detailed description

### Development Setup

```bash
# Clone and setup
git clone https://github.com/your-org/braas-ai-pipeline.git
cd braas-ai-pipeline
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=braas --cov-report=html tests/
```

### Coding Standards

- Follow PEP 8 with line length of 100 characters
- Use type hints throughout
- Write async code with asyncio
- Add tests for all new functionality
- Document public APIs with docstrings

## Roadmap

### v0.2.0 (Planned)
- [ ] Additional experiment types (Western Blot, Flow Cytometry)
- [ ] Machine learning model for parameter optimization
- [ ] Enhanced WebSocket support for real-time collaboration
- [ ] Graph visualization of experiment relationships

### v0.3.0 (Planned)
- [ ] Multi-lingual NLP support
- [ ] Advanced reagent inventory management
- [ ] Predictive equipment maintenance scheduling
- [ ] Integration with additional LIMS systems

### v0.4.0 (Planned)
- [ ] Federated learning for model improvement
- [ ] Natural language query interface for results
- [ ] Automated manuscript generation
- [ ] Enhanced visualization dashboard

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## GitHub

**Repository**: https://github.com/your-org/braas-ai-pipeline

For issues, feature requests, and contributions, please use the GitHub issue tracker.

---

*BRaaS - Empowering Biological Research with AI*
