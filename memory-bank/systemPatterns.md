# System Patterns: L2 Medical Information System

> **Language Requirement:** All Memory Bank documentation must be written in English.
> New entries, updates, and modifications must be in English.

## Architecture

### Architectural Style
- **Monolithic architecture** with modular Django apps
- **Micro-frontends** via Vue.js components
- **Asynchronous processing** via Celery for long operations
- **REST API** for frontend-backend communication

### Layers
```
┌─────────────────────────────────────┐
│   Presentation Layer (Vue.js)       │
├─────────────────────────────────────┤
│   API Layer (Django REST Framework) │
├─────────────────────────────────────┤
│   Business Logic Layer (Views)      │
├─────────────────────────────────────┤
│   Data Access Layer (Models)        │
├─────────────────────────────────────┤
│   Database (PostgreSQL)             │
└─────────────────────────────────────┘
```

## Key Design Patterns

1. **MVT (Model-View-Template)** - Django's core pattern
2. **Repository Pattern** - SQL functions in `sql_func.py`, custom managers
3. **Service Layer** - Business logic in `utils.py`, `manager.py` modules
4. **Factory Pattern** - Complex object creation (referrals, documents, forms)
5. **Strategy Pattern** - Different processing based on type (lab/paraclinical, research types, integrations)
6. **Observer Pattern** - Django Signals for auto-logging, triggers, `slog` module
7. **Command Pattern** - Django management commands, Celery tasks, API endpoints

## Domain-Driven Module Organization

### Client Domain
- `clients/` - patients and cards

### Medical Domain
- `directions/` - referrals
- `researches/` - research types
- `directory/` - research directories
- `results/` - research results
- `receivematerial/` - biomaterial reception

### Organizational Domain
- `podrazdeleniya/` - departments
- `hospitals/` - hospitals
- `users/` - users and doctor profiles
- `employees/` - staff
- `doctor_schedule/` - schedules

### Clinical Domain
- `doctor_call/` - house calls
- `cases/` - treatment cases
- `stationar/` - inpatient (via api/stationar/)
- `pharmacotherapy/` - pharmacotherapy
- `medical_certificates/` - medical certificates
- `treatment/` - treatment

### Financial Domain
- `contracts/` - contracts
- `cash_registers/` - cash operations
- **CITO pricing:** `PriceCoast.coast_cito` on the same price row; `PriceCoast.resolve_coast(coast, coast_cito, is_cito)` returns CITO price when `is_cito` and `coast_cito > 0`, else base `coast`. Direction creation passes `is_cito` into `gen_napravleniya_by_issledovaniya` so `Issledovaniya.coast` is set correctly at creation.

### Analytics Domain
- `statistic/` - statistics
- `reports/` - reports
- `dashboards/` - dashboards
- `statistics_tickets/` - ticket statistics
- Statistics UI catalog lives in `l2-frontend/src/pages/Statistics.vue` (`STATS_CATEGORIES`); each report `type` is handled in `statistic/views.py`
- Report `unlimitPeriod: true` skips the 2-month date range check on the frontend; backend excludes that `type` from the 60-day cap
- Epid numbers report (`statistics-epid-numbers`) reuses `forms.views.get_epid_data` for extra-notification slave directions confirmed in the period

### Integration Domain
- `integration_framework/` - integration framework
- `rmis_integration/` - RMIS
- `external_system/` - external systems
- `ecp_integration/` - digital signatures
- `ftp_orders/` - FTP orders
- `results_feed/` - result transmission

### Document Flow
- `forms/` - document templates
- `construct/` - form constructor
- `document_management/` - document management

## Data Patterns

### Entity Relationships
```
Card (Patient)
  ↓ 1:N
Napravleniya (Referral)
  ↓ 1:N
Issledovaniya (Research)
  ↓ 1:N
Result (Result)
```

### Key Patterns
- **Soft Delete** - `hide`, `cancel` flags instead of physical deletion
- **Audit Trail** - `slog/` module, `create_at`, `who_create` fields
- **Multi-tenancy** - Support for multiple hospitals via `Hospitals`, data filtering by organization

## Integration Patterns

- **Adapter Pattern** - RMIS adapter, HL7 adapter (hl7apy), ASTM adapter (lab equipment), SOAP adapter (zeep)
- **Queue Pattern** - Celery for async processing, queues for external system data sending
- **Webhook Pattern** - API endpoints for external system data reception
- **REST result pull daemons** (`daemons/`): `rest_api_pull_result_start` runs once a day at `REST_API_PULL_RESULT_RUN_TIME` (`HH:MM`, `TIME_ZONE`); `rest_api_get_new_results_start` asks each hospital API `GET_NEW_RESULTS` then runs `_run_pull_for_orders`. Interval: `REST_API_GET_NEW_RESULTS_INTERVAL_SECONDS`. Per-hospital auth from `Hospitals.auth_data_for_rest`. REST keys are cached per hospital (`{hospital_id}_hosp_key_auth`), TTL `REST_API_HOSPITAL_KEY_TTL_MINUTES` (default `5 * 24 * 60`, overridable in `local_settings.py`).

## Document Generation Patterns

- **Template Method** - Base templates for document types
- **Builder** - Step-by-step complex document construction (PDF, DOCX via reportlab, python-docx)
- **Form Constructor** - Dynamic form creation via `construct/`, JSON-based configuration

## Security Patterns

- **RBAC (Role-Based Access Control)** - Django groups, roles (doctor, lab tech, registrar, admin)
- **Authentication** - Django Auth, 2FA (pyotp, QR codes), digital signatures for documents
- **Data Protection** - Sensitive data encryption, patient data protection, CORS for API

## Performance Patterns

- **Caching** - Redis, Memcached for sessions, DB-level caching
- **Eager Loading** - `select_related`, `prefetch_related`, `api/prefetch.py` for query optimization
- **Pagination** - For large lists, lazy loading for heavy data
- **DB Optimization** - Indexes (`db_index=True`), denormalization where needed, raw SQL for complex analytics

## UI/UX Patterns

- **Component-Based Architecture** - Reusable Vue.js components, isolated logic, props for data passing
- **State Management** - Vuex for global state, local component state
- **Progressive Enhancement** - Basic functionality without JS, enhanced with JS

## Testing Patterns

- **Test Organization** - Unit tests in `__spec__/` directory
- **Fixtures** - Django fixtures, factories for test objects

## Code Conventions

### Python Code Style
- Black formatter (line-length: 190)
- Flake8 linter
- Type hints where possible

### Naming
- `snake_case` - variables, functions
- `PascalCase` - classes
- `UPPER_CASE` - constants

### File Organization
```
module_name/
├── __init__.py
├── models.py          # Data models
├── views.py           # Views/controllers
├── urls.py            # URL routing
├── admin.py           # Django admin
├── sql_func.py        # SQL functions
├── utils.py           # Utilities
├── migrations/        # DB migrations
├── management/        # Management commands
└── __spec__/          # Tests
```

## Anti-patterns to Avoid

1. **God Objects** - Keep models focused
2. **Tight Coupling** - Modules should be independent
3. **Hard-coded Values** - Use appconf settings
4. **N+1 Queries** - Use prefetch/select_related
5. **Magic Numbers** - Use constants
