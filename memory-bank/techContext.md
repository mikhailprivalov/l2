# Technical Context: L2 Medical Information System

> **Language Requirement:** All Memory Bank documentation must be written in English.
> New entries, updates, and modifications must be in English.

## Technology Stack

### Backend
- **Django 4.1** (Python >=3.8, <4.0)
- **PostgreSQL** - primary database (psycopg2)
- **Django REST Framework 3.14** - REST API

### API & Integrations
- **zeep 4.1** - SOAP client
- **requests 2.28** - HTTP requests
- **hl7apy 1.3** - HL7 protocol
- **astm** (custom fork) - lab equipment protocol

### Async Tasks
- **Celery 5.3.6** - task queue (Python 3.12 compatible)
- **Redis 4.4.4** - Celery broker & caching
- **django-celery-results 2.5.1** - task result storage

### Document Generation
- **reportlab 4.0.7** - PDF generation
- **openpyxl 3.1.2** - Excel
- **python-docx 0.8.11** - Word documents
- **pdfkit 1.0.0** - HTML to PDF conversion
- **PyPDF2 1.28.6** - PDF manipulation

### Security & Auth
- **pyotp 2.8** - OTP (2FA)
- **qrcode 7.4** - QR code generation
- **cryptography 41** - Fernet encryption helpers

### Utilities
- **pytils 0.3, transliterate 1.10.2** - transliteration
- **petrovna 1.0.2** - Russian name declension
- **python-dateutil 2.8.2** - date handling
- **anytree 2.8.0** - tree structures

### Development & Code Quality
- **black 23.3.0** - code formatting
- **flake8-black 0.3.6** - linter
- **autopep8 1.7.0** - auto-formatting

### Web Server & Monitoring
- **gunicorn 20.1.0** - WSGI HTTP server
- **gevent 23.9.1** - async
- **django-prometheus 2.3.1** - Prometheus metrics

### Caching & Cloud
- **pymemcache 4.0.0** - Memcached client
- **django-cors-headers 3.13.0** - CORS support
- **boto3 1.29.3** - AWS SDK (S3 for file storage)

### Frontend
- **Vue.js 2.7** - main framework with Composition API (Vue 3 compatibility mode)
- **TypeScript** - strict typing
- **CRITICAL:** All new code uses `<script setup>` with Composition API
- **Webpack** - module bundler
- **django-webpack-loader 1.6.0** - Django/Webpack integration
- **Yarn** - package manager (NOT npm!)
- Code location: `l2-frontend/`

### External Systems & Protocols
- RMIS (Regional Medical Information System)
- Digital signature integration
- REST API, SOAP (zeep), HL7, ASTM, FTP

## Project Structure

```
l2/
├── api/                    # REST API endpoints
├── clients/                # Patient module
├── directions/             # Referrals
├── directory/              # Directories
├── researches/             # Research
├── laboratory/             # Lab functions
├── results/                # Research results
├── users/                  # Users & doctors
├── podrazdeleniya/         # Departments
├── hospitals/              # Hospitals
├── contracts/              # Contracts
├── integration_framework/  # Integration framework
├── rmis_integration/       # RMIS integration
├── external_system/        # External systems
├── forms/                  # Document forms
├── reports/                # Reports
├── statistic/              # Statistics
├── dashboards/             # Dashboards
├── l2-frontend/            # Vue.js frontend
├── memory-bank/            # Documentation (Memory Bank)
└── ...
```

## Infrastructure

### Database
- PostgreSQL as primary storage
- Django ORM migrations
- SQL functions in `sql_func.py` modules

### Caching & Background Jobs
- Redis for Celery & caching
- Memcached (optional)
- Celery + Redis for async tasks

### File Storage
- Local filesystem (media/)
- AWS S3 for cloud storage (boto3)

### Monitoring & Logging
- django-prometheus for metrics
- Django standard logging
- `slog` module for system logs

## Development Setup

### Dependency Management
- **Poetry** - Python dependencies (pyproject.toml, poetry.lock)
- **Yarn** - JavaScript dependencies (NOT npm!)

### Development Scripts
- `frontend_watch.sh` - frontend watch mode
- `frontend_hmr.sh` - Hot Module Replacement
- `manage.py` - Django management

### Versioning
- Git version control
- Scripts: `current-version.sh`, `update-version.sh`, `do-release.sh`
- Current version in pyproject.toml: `2025.10.41221+61efaf`

### CI/CD
- GitHub Actions: flake8, Vue CLI linter, CodeQL analysis

## Configuration

### Settings
- `laboratory/settings.py` - main Django settings
- `local_settings.py` - local settings (ignored in git)
- `.env` files - environment variables
- `appconf` module - DB-based settings management via `SettingManager`

## Environment Requirements

- **Python:** >=3.8, <4.0
- **PostgreSQL:** latest stable recommended
- **Node.js:** for frontend build
- **OS:** Linux (production), macOS/Windows supported for development
