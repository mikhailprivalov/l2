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
- **Gardening electricity:** `GardeningElectricityMeter` is the single plot-level meter list with optional `date_start` / `date_end`. Each meter also stores subscriber address, subscriber name, device type, and serial number — edited in the meter modal from both the owner form and electricity readings. Owner modal and electricity readings both read/write that model; meters are not deleted — they are closed by end date. `_ensure_meters` creates «Счётчик 1» if none exist. `GardeningElectricityMeterReading` belongs to a meter. The year table and PDF only include months that overlap the meter period. Charge is per active meter. **Списано** is also per meter: the plot write-off (`min(available, total charge)`) is allocated across meters in display order, each row up to its own charge. **Приход / Долг / Остаток** stay plot-level and are shown on the first active meter of that month (and on the month total). Missing tariff is red `0.00`. Current reading cannot be less than previous (equal is allowed); create/update reading APIs and both UIs (plot table, month list, previous-reading modal) enforce this. UI: `/ui/gardening` object panel, plus to add a meter, pencil modal for dates. Owner table is full width (10px right inset) and includes email (`OwnersRealEstate.email`) and plot area (`RealEstate.area`). Plot area and email are edited in the owner add/edit modal.
- **Gardening plot contributions:** Object panel shows a **Взносы** table on the same row as **Приход (Банк)** (each 50%), below the owner. Rows are year payment types except electricity and `not_control`. Columns: title, tariff (year overlapping rate), coefficient (`1` for absolute / neither, plot `RealEstate.area` for `is_by_area`), charged, written-off, debt, remainder. Money uses the electricity remainder rule (`available = previous remainder + bank receipts`, written-off = min(available, charge), debt = shortfall, remainder ≥ 0). Yearly period charges the overlapping rate once; monthly period sums 12 monthly rates. `is_by_area` charges **rate × area**. Missing tariff, area (for by-area), or charge is red `0.00`. Plot area (m²) is edited in the owner add/edit modal and saved on `RealEstate`. API: `gardening/get-plot-contributions`. The table refreshes when bank receipts or owner/area change. PDF `115.01` prints this table after bank receipts and before electricity.
- **Gardening accounting (Все):** In Учёт mode with «Все» selected, the header shows year payment types. If the selected type is electricity (`is_use_kilowatt` or title contains «электроэнергия»), a January–December month strip appears below the types. Clicking a month opens `GardeningElectricityMonthList`: one row per active meter across plots (plot, meter, previous/current readings with date headers, consumption, tariff, charge, written-off, plot totals: consumption, written-off, debt, remainder, receipt). Plot-total columns (`* общ`) show values only on the first visible row of each plot after filters/sort. Column sort; filters for debt and missing current reading. Inline reading edit uses the same create/update reading APIs as the plot electricity table. API: `gardening/get-electricity-month-rows`. Other payment types (except `not_control`) open `GardeningAccountingSummary` in table mode: one row per plot with the same fields and formulas as plot **Взносы** (`_contribution_row`): tariff, coefficient, charge, written-off, debt, remainder. Missing tariff/area/charge is red `0.00`. Column sort and a debt filter. «Итого» still lists types with bank receipt totals. API: `gardening/get-accounting-summary`.

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
- **JSON order export daemon** (`daemons/ftp_push_json_orders_start.py` → `ftp_orders/json_export.py`): `api/requests/create` writes `{pk}_{YYYYMMDD}_{HHMMSSmmm}_ord.json`, `api/requests/link-image` (link branch only) writes `{pk}_{YYYYMMDD}_{HHMMSSmmm}_{studyInstanceUID}_dcm.json`. Payload holds every `Napravleniya` concrete field plus the `_l2_file_type` tag (`ord`/`dcm`). `ord` also adds `family`, `name`, `patronymic`, `birthday`, `sex`, `doctor_id`, `uuid` (`DoctorProfile.uuid` of the creating doctor), `hospital_oid`, `internal_code` (first research), and active `documents` (`type`, `serial`, `number`) from related patient/hospital. `dcm` adds `uuid` (`Equipment.uuid`), `hospital_oid`, `study_instance_uid`, and `EquipmentReceive` patient/DICOM tag metadata. Views only spool atomically (`.tmp` + `os.replace`) to `FTP_JSON_ORDERS_SPOOL_DIR` (default `<BASE_DIR>/ftp_json_spool`); the daemon uploads to `FTP_JSON_ORDERS_URL` every `FTP_JSON_ORDERS_INTERVAL_SECONDS` and after a successful `STOR` moves the file to `FTP_JSON_ORDERS_ARCHIVE_DIR` (default `<BASE_DIR>/ftp_json_archive`). Empty URL disables upload; all settings live in `laboratory/settings.py`, overridable in `local_settings.py`.
- **JSON order import daemon** (`daemons/ftp_pull_json_orders_start.py` → `ftp_orders/json_import.py`): polls `FTP_JSON_ORDERS_PULL_URL` (must not equal the push URL). `_ord.json` / `_l2_file_type=ord` creates a request (`id_in_hospital` = source `id`, research by `internal_code`, doctor by `uuid` then `doctor_id`, patient by documents then FIO+DOB+sex); `_dcm.json` finds local `Equipment` by `uuid`, deletes any existing `EquipmentReceive` with the same `study_instance_uid` and equipment, creates a new one from payload metadata, and links it to the request. Successful files are deleted on FTP; failures stay for retry. Same functions are exposed as token APIs under `integration_framework/dicom/`: `json-order-create`, `json-study-link`, `json-order-get`. Import does not spool outgoing JSON.
- **JSON result export/import:** after a direction is fully confirmed, `Napravleniya.post_confirmation` synchronously spools `{id}_{YYYYMMDD}_{HHMMSSmmm}_res.json` when `hospital.json_result_auto_export` is true. `id` is `id_in_hospital` if set, otherwise the direction `pk`. Payload is `_l2_file_type=res`, `id`, `pdf` (base64), `time_confirmation`, `doctor_fio`. Spool/archive dirs are `FTP_JSON_RESULTS_SPOOL_DIR` / `FTP_JSON_RESULTS_ARCHIVE_DIR` (defaults `<BASE_DIR>/ftp_json_results_spool` and `ftp_json_results_archive`). Daemon `ftp_push_json_results_start` uploads to `FTP_JSON_RESULTS_URL`; `ftp_pull_json_results_start` and token API `json-result-create` apply the result to the original request (`pk=id`): PDF on `IssledovaniyaFiles`, `time_confirmation`, `doc_confirmation_string`.
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
- **TwoSidedLayout** - fixed left width (`leftWidthPx`); `resizable` adds a col-resize gutter, emits `update:left-width-px`, clamps min left/right. Other pages keep a static split unless they opt in.

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
