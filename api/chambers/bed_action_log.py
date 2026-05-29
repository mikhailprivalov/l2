from podrazdeleniya.models import Bed, PatientBedActionLog, PatientToBed


def log_bed_action(
    action,
    *,
    author,
    department_id=None,
    direction_id=None,
    bed_id=None,
    doctor_id=None,
    patient_to_bed=None,
    patient_to_bed_pk=None,
    plan_date_in=None,
    plan_date_out=None,
    patient_fio_text="",
    is_extract=False,
    payload=None,
):
    if patient_to_bed is not None and isinstance(patient_to_bed, PatientToBed):
        if patient_to_bed_pk is None:
            patient_to_bed_pk = patient_to_bed.pk
        if bed_id is None:
            bed_id = patient_to_bed.bed_id
        if direction_id is None:
            direction_id = patient_to_bed.direction_id
        if doctor_id is None:
            doctor_id = patient_to_bed.doctor_id
        if not plan_date_in:
            plan_date_in = patient_to_bed.plan_date_in
        if not plan_date_out:
            plan_date_out = patient_to_bed.plan_date_out
        if not patient_fio_text:
            patient_fio_text = patient_to_bed.patient_fio_text or ""
        if not is_extract:
            is_extract = bool(patient_to_bed.is_extract)

    if bed_id is not None and not Bed.objects.filter(pk=bed_id).exists():
        bed_id = None

    PatientBedActionLog.objects.create(
        action=action,
        author=author,
        department_id=department_id,
        direction_id=direction_id,
        bed_id=bed_id,
        doctor_id=doctor_id,
        patient_to_bed=patient_to_bed if isinstance(patient_to_bed, PatientToBed) else None,
        patient_to_bed_pk=patient_to_bed_pk,
        plan_date_in=plan_date_in,
        plan_date_out=plan_date_out,
        patient_fio_text=(patient_fio_text or "")[:128],
        is_extract=bool(is_extract),
        payload=payload or {},
    )
