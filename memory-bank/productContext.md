# Product Context: L2 Medical Information System

> **Language Requirement:** All Memory Bank documentation must be written in English.
> New entries, updates, and modifications must be in English.

## Problems Solved

1. **Fragmented Medical Data** - No unified patient information storage, paper cards get lost, difficult to track visit history
2. **Inefficient Manual Processes** - Time-consuming manual referral forms, lost referrals between departments, data duplication
3. **Laboratory Complexity** - Manual test result entry, transcription errors, quality control difficulties
4. **Lack of Real-time Analytics** - Can't quickly get statistics, complex report generation, no doctor workload monitoring
5. **Integration Issues** - Need for external system interaction (RMIS, etc.), data duplication across systems, data inconsistency

## Core Workflows

**Main Flow:** Patient → Registration → Doctor → Referrals → Lab/Paraclinical → Results → Doctor → Patient

### Key User Scenarios

1. **Patient Registration & Admission** - Registrar creates/finds patient card → schedules appointment → doctor examines, diagnoses → creates referrals
2. **Laboratory Testing** - Patient provides biomaterial → lab tech receives in system → conducts tests (with auto-load from equipment) → results auto-populate → doctor accesses results
3. **House Calls** - Call request (phone/online) → dispatcher creates call → assigns doctor → doctor sees in schedule → fills call card after visit
4. **Inpatient Treatment** - Admission → medical history management → prescriptions/procedures → patient discharge
5. **Reporting** - Auto-generate statistical reports → export to external systems → monitor performance metrics

## System Principles

1. **Single Data Entry Point** - Information entered once, available across all modules, auto-propagation of changes
2. **Role-Based Access** - Users see only what they need; doctors see their patients, lab techs work with materials/results, admins manage directories
3. **Traceability** - All actions logged, change history preserved, full referral tracking from creation to result
4. **Integration-Ready** - Open API, standard protocol support (HL7, ASTM), multiple data export formats
5. **Configuration Flexibility** - Customizable directories, form constructor, access rights configuration, system parameterization per facility

## Target User Experience

- **Doctors:** Fast patient info access, simple referral creation, auto-suggestions/templates, minimal clicks for routine tasks
- **Lab Technicians:** Quick material reception (barcode scanning), auto-load results from equipment, QC at each stage, convenient manual result entry
- **Registrars:** Fast patient registration, simple schedule management, print referrals/documents
- **Administrators:** Full system control, flexible settings, clear reports/analytics, system monitoring

## Quality Criteria

- **Performance:** UI response < 1 sec for most operations, handle thousands of patients daily, scalable under load
- **Reliability:** 99.9%+ availability, data backups, data loss protection
- **Usability:** Intuitive interface, minimal training required, hotkey support for experienced users
- **Security:** Patient data protection, role-based access model, full action audit, digital signature support

