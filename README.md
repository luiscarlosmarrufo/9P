# 9P Social Analytics Platform

A production-grade social analytics platform for ingesting and analyzing Twitter/X and Reddit content using multi-label 9P classification and sentiment analysis.

## Architecture Overview

- **Data Ingestion**: Twitter/X and Reddit APIs
- **Classification**: Two-stage inference (embeddings + LogisticRegression → vLLM fallback)
- **Storage**: S3 (raw JSON), PostgreSQL (normalized data), Redis (jobs/cache)
- **API**: FastAPI REST endpoints
- **UI**: Streamlit dashboard (MVP, contract-ready for Next.js)
- **Infrastructure**: AWS with Terraform, ECS Fargate, EC2 ASG

## 9P Framework

Multi-label classification into:
- **Product**: Features, quality, functionality
- **Place**: Distribution, availability, location
- **Price**: Cost, value, pricing strategy
- **Publicity**: Marketing, advertising, promotion
- **Post-consumption**: Reviews, feedback, experience
- **Purpose**: Brand mission, values, social impact
- **Partnerships**: Collaborations, endorsements
- **People**: Customer service, community, staff
- **Planet**: Sustainability, environmental impact

## Quick Start

### Local Development

```bash
# Clone and setup
git clone <repo-url>
cd 9P
make setup

# Start services
make compose-up

# Run tests
make test

# Format and lint
make format
make lint
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### API Endpoints

- `POST /v1/ingest/twitter` - Ingest Twitter/X data
- `POST /v1/ingest/reddit` - Ingest Reddit data
- `POST /v1/classify/run` - Run classification job
- `GET /v1/summary/monthly` - Monthly summaries
- `GET /v1/items` - Query classified items
- `GET /v1/export/csv` - Export data as CSV
- `GET /v1/health` - Health check
- `GET /v1/metrics` - System metrics

### Streamlit Dashboard

Access at `http://localhost:8501`:
- **Overview**: High-level metrics and trends
- **Deep Dive**: Detailed analysis with filters
- **Compare Brands**: Brand comparison views
- **Exports**: Data export functionality

## Deployment

### AWS Infrastructure

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

### CI/CD

GitHub Actions automatically:
- Runs tests and linting
- Builds Docker images
- Deploys to AWS ECS with blue/green strategy

## Project Structure

```
9P/
├── infra/terraform/          # AWS infrastructure as code
├── docker/                   # Docker configurations
├── control/                  # FastAPI application
├── worker/                   # Celery background tasks
├── inference/                # vLLM inference server
├── ml/                       # Machine learning models
├── web/                      # Streamlit dashboard
├── tests/                    # Test suites
├── .github/workflows/        # CI/CD pipelines
└── docs/                     # Documentation
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Celery, SQLAlchemy
- **ML**: sentence-transformers, scikit-learn, vLLM
- **Data**: PostgreSQL, Redis, AWS S3
- **Infrastructure**: AWS ECS, RDS, ElastiCache, Terraform
- **CI/CD**: GitHub Actions, AWS CodePipeline
- **Quality**: ruff, black, mypy, pytest, pre-commit

## Contributing

1. Install pre-commit hooks: `pre-commit install`
2. Follow the coding standards (enforced by ruff/black/mypy)
3. Add tests for new features
4. Update documentation as needed

## License

[License information]
