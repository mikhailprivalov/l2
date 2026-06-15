import base64
from io import BytesIO

import pyotp
import qrcode
from django.contrib.auth.decorators import login_required

from l2vi.integration import check_doctor_data
from laboratory.decorators import group_required
from laboratory.settings import SHOW_RMIS_CHANGE_PASSWORD
import simplejson as json
import re
from random import randint

from django.contrib.auth import authenticate, login
from django.db import transaction

from contracts.models import PriceName, PriceCoast
from directory.models import Researches
from hospitals.models import Hospitals
from laboratory.settings import GROUP_USER_FOR_FILTER
from laboratory.utils import current_time
from users.tasks import send_password_reset_code

from utils.response import status_response
import slog.models as slog
from users.models import DoctorProfile, DoctorProfileEcpPosition
from django.http import JsonResponse


def auth(request):
    data = json.loads(request.body)
    username = data.get('username', '')
    password = data.get('password', '')
    totp_password = data.get('totp', '')
    user = authenticate(username=username, password=password)
    f1 = re.findall(r"^([ X0-9]{5})([0-9a-fA-F]{5})$", username)
    if user:
        ip = slog.Log.get_client_ip(request)
        if not totp_password and user.doctorprofile.totp_secret:
            return status_response(False, data={"totp": True})

        if not user.doctorprofile.check_totp(totp_password, ip):
            return status_response(False, message="Неверный код двухфакторной аутентификации")
        if user.doctorprofile.dismissed:
            return status_response(False, message="Не активный пользователь")

        if user.doctorprofile.hospital.hide:
            return status_response(False, message="Организация не активна")

        if user.is_active:
            login(request, user)
            log = slog.Log(key="", type=18, body="IP: {0}".format(ip), user=request.user.doctorprofile)
            log.save()
            request.user.doctorprofile.register_login(ip)
            return status_response(
                True,
                data={
                    'fio': user.doctorprofile.get_full_fio(),
                    'orgId': user.doctorprofile.get_hospital_full_id(),
                    'orgTitle': user.doctorprofile.get_hospital_title(),
                    'userId': user.doctorprofile.pk,
                },
            )

        return status_response(False, message="Ваш аккаунт отключен")
    elif len(password) == 0 and len(f1) == 1 and len(f1[0]) == 2:
        did = int(f1[0][0].replace("X", ""))
        u = DoctorProfile.objects.filter(pk=did).first()
        if u and u.get_login_id() == username and u.user.is_active and not u.user.is_staff:
            user = u.user
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            slog.Log(key='По штрих-коду', type=18, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile).save()
            request.user.doctorprofile.register_login(slog.Log.get_client_ip(request))
            return status_response(True, data={'fio': user.doctorprofile.get_full_fio()})

    return status_response(False, message="Неверное имя пользователя или пароль")


def loose_password(request):
    if request.user.is_authenticated:
        return status_response(False)
    data = json.loads(request.body)
    step = data.get('step')
    email = data.get('email')
    code = data.get('code')
    if email:
        email = email.strip()
    if code:
        code = code.strip()
    if step == 'request-code':
        if email and DoctorProfile.objects.filter(email__iexact=email).exists():
            doc: DoctorProfile = DoctorProfile.objects.filter(email__iexact=email)[0]
            request.session['email'] = email
            request.session['code'] = str(randint(10000, 999999))
            send_password_reset_code.delay(email, request.session['code'], doc.hospital_safe_title)
            slog.Log(key=email, type=121000, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=doc).save()
        return status_response(True)
    elif step == 'check-code':
        if email and DoctorProfile.objects.filter(email__iexact=email).exists() and request.session.get('email') == email and code and request.session.get('code') == code:
            doc: DoctorProfile = DoctorProfile.objects.filter(email__iexact=email)[0]
            doc.reset_password()
            slog.Log(key=email, type=121001, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=doc).save()
            request.session['email'] = None
            request.session['code'] = None
            return status_response(True)
    return status_response(False)


@login_required
def change_password(request):
    doc: DoctorProfile = request.user.doctorprofile
    doc.reset_password()
    slog.Log(key='', type=120000, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile).save()
    return status_response(True)


@login_required
def set_password(request):
    data = json.loads(request.body)
    old_password = data.get('oldPassword', '')
    new_password = data.get('newPassword', '')
    confirm_password = data.get('confirmPassword', '')

    if len(new_password) < 6:
        return status_response(False, message='Пароль должен содержать минимум 6 символов')
    if new_password != confirm_password:
        return status_response(False, message='Пароли не совпадают')
    if not request.user.check_password(old_password):
        return status_response(False, message='Неверный текущий пароль')

    request.user.set_password(new_password)
    request.user.save()
    slog.Log(key='', type=120000, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile).save()
    return status_response(True)


def _serialize_ecp_position(position: DoctorProfileEcpPosition):
    return {
        'id': position.pk,
        'type_medical_form': position.type_medical_form,
        'arm_type': position.arm_type or '',
        'med_staff_fact_id': position.med_staff_fact_id or '',
        'lpu_section_id': position.lpu_section_id or '',
        'lpu_section_name': position.lpu_section_name or '',
        'med_staff_fact_stavka': position.med_staff_fact_stavka or '',
    }


def _normalize_type_medical_form(value):
    if value in (None, '', -1, '-1', 'unset'):
        return None
    if value in ('emergency', '0', 0):
        return 0
    if value in ('stationary', '1', 1):
        return 1
    return int(value)


def _validate_unique_type_medical_form(ecp_positions):
    seen = {}
    labels = {0: 'Экстренная служба', 1: 'Стационар'}
    for item in ecp_positions:
        type_medical_form = _normalize_type_medical_form(item.get('type_medical_form'))
        if type_medical_form is None:
            continue
        if type_medical_form in seen:
            return False, f'Тип медпомощи «{labels[type_medical_form]}» указан более одного раза'
        seen[type_medical_form] = True
    return True, None


def _get_ecp_position_rows(doc: DoctorProfile):
    return [
        _serialize_ecp_position(position)
        for position in DoctorProfileEcpPosition.objects.filter(doctor_profile=doc).order_by('id')
    ]


@login_required
def get_ecp_positions(request):
    if not SHOW_RMIS_CHANGE_PASSWORD:
        return status_response(False, message='Функция недоступна')

    doc: DoctorProfile = request.user.doctorprofile
    rows = _get_ecp_position_rows(doc)
    return status_response(True, data={
        'rows': rows,
        'rmis_password_hint': doc.get_rmis_password_hint(),
    })


@login_required
def set_rmis(request):
    if not SHOW_RMIS_CHANGE_PASSWORD:
        return status_response(False, message='Функция недоступна')

    data = json.loads(request.body)
    rmis_login = (data.get('rmis_login') or '').strip() or None
    rmis_password = (data.get('rmis_password') or '').strip() or None
    ecp_positions = data.get('ecp_positions') or []

    doc: DoctorProfile = request.user.doctorprofile
    ok, message = _validate_unique_type_medical_form(ecp_positions)
    if not ok:
        return status_response(False, message=message)

    doc.rmis_login = rmis_login
    if rmis_password:
        doc.rmis_password = rmis_password
    elif not rmis_login:
        doc.rmis_password = None
    doc.save(update_fields=['rmis_login', 'rmis_password'])

    for item in ecp_positions:
        position_id = item.get('id')
        if not position_id:
            continue
        type_medical_form = _normalize_type_medical_form(item.get('type_medical_form'))
        DoctorProfileEcpPosition.objects.filter(pk=position_id, doctor_profile=doc).update(type_medical_form=type_medical_form)

    slog.Log(key='', type=120000, body="IP: {0}, RMIS".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile).save()
    return status_response(True, data={
        'rmis_login': doc.rmis_login or '',
        'rmis_password_hint': doc.get_rmis_password_hint(),
    })


@login_required
def check_rmis(request):
    if not SHOW_RMIS_CHANGE_PASSWORD:
        return status_response(False, message='Функция недоступна')

    data = json.loads(request.body) if request.body else {}
    doc_profile = request.user.doctorprofile
    rmis_login = (data.get('rmis_login') or '').strip() or doc_profile.rmis_login
    rmis_password = (data.get('rmis_password') or '').strip() or doc_profile.rmis_password

    if not rmis_login:
        return status_response(False, message='Укажите логин РМИС')

    message = "Успех"
    result = check_doctor_data({"docLogin": rmis_login, "docPassword": rmis_password})
    if result.get("success"):
        ok = True
        DoctorProfileEcpPosition.objects.filter(doctor_profile=doc_profile).delete()
        for i in result.get('arms', []):
            if i.get('ARMType') == 'stac6' or i.get('ARMType') == 'htm':
                continue
            DoctorProfileEcpPosition(
                doctor_profile=doc_profile,
                arm_type=i.get('ARMType'),
                arm_name=i.get('ARMName'),
                med_personal_id=i.get('MedPersonal_id'),
                med_staff_fact_id=i.get('MedStaffFact_id'),
                lpu_section_profile_id=i.get('LpuSectionProfile_id'),
                lpu_section_id=i.get('LpuSection_id'),
                lpu_section_name=i.get('LpuSection_Name'),
                med_staff_fact_stavka=i.get('MedStaffFact_Stavka'),
                med_personal_FIO=i.get('MedPersonal_FIO'),
                post_med_name=i.get('PostMed_Name'),
                org_id=i.get('Org_id'),
                lpu_id=i.get('Lpu_id'),
            ).save()
        rows = _get_ecp_position_rows(doc_profile)
    else:
        ok = False
        message = "Не успех"
        rows = []
    return status_response(ok, message=message, data={'rows': rows})


@login_required
def set_new_email(request):
    data = json.loads(request.body)
    step = data.get('step')
    new_email = data.get('newEmail')
    confirmation_code = data.get('confirmationCode')
    new_confirmation_code = data.get('newConfirmationCode')
    doc: DoctorProfile = request.user.doctorprofile

    if new_email:
        new_email = new_email.strip()

    def check_new_email_is_free():
        return not DoctorProfile.objects.filter(email__iexact=new_email).exists()

    def check_new_email_is_valid():
        return bool(new_email)

    def check_old_email_code():
        return doc.check_old_email_code(confirmation_code, request)

    def new_email_has_error():
        if not check_old_email_code():
            return 'Некорректный код со старого email'
        if not check_new_email_is_valid():
            return 'Некорректный адрес'
        if not check_new_email_is_free():
            return f'Адрес {new_email} занят'
        return None

    if step == 'set-new-email':
        new_email_error = new_email_has_error()
        if new_email_error:
            return status_response(False, message=new_email_error)
        else:
            doc.new_email_send_code(new_email, request)
            return status_response(True)

    if step == 'confirm-new-email':
        new_email_error = new_email_has_error()
        if new_email_error:
            return status_response(False, message=new_email_error)
        check_new_email_code = doc.new_email_check_code(new_email, new_confirmation_code, request)
        if check_new_email_code:
            old_email = doc.email
            doc.set_new_email(new_email, request)
            slog.Log(
                key=new_email,
                type=120001,
                body=json.dumps(
                    {
                        "ip": slog.Log.get_client_ip(request),
                        "old": old_email,
                        "new": new_email,
                    }
                ),
                user=request.user.doctorprofile,
            ).save()
            return status_response(True)
        else:
            return status_response(False, message='Некорректный код')

    if step == 'request-code':
        doc.old_email_send_code(request)
        return status_response(True)

    if step == 'check-code':
        status = doc.check_old_email_code(confirmation_code, request)
        if status:
            return status_response(True)
        else:
            return status_response(False, message='Некорректный код со старого email')

    return status_response(False)


@login_required
def generate_totp_code(request):
    doc: DoctorProfile = request.user.doctorprofile

    if doc.totp_secret:
        return status_response(False, message='Двухфакторная аутентификация уже включена')

    secret_code = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret_code).provisioning_uri(
        name=doc.fio,
        issuer_name=f"L2 {doc.hospital_safe_title}",
    )
    qr = qrcode.make(uri)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())

    return status_response(
        True,
        data={
            'secretCode': secret_code,
            'qrCode': f"data:image/png;base64,{img_str.decode('utf-8')}",
        },
    )


@login_required
def set_totp(request):
    data = json.loads(request.body)
    secret_code = data.get('secretCode')
    confirmation_code = data.get('confirmationCode')
    doc: DoctorProfile = request.user.doctorprofile
    if doc.totp_secret:
        return status_response(False, message='Двухфакторная аутентификация уже включена')
    if not secret_code:
        return status_response(False, message='Некорректный код')
    if not confirmation_code:
        return status_response(False, message='Некорректный код')
    with transaction.atomic():
        doc.totp_secret = secret_code
        doc.save()
        ip = slog.Log.get_client_ip(request)
        if not doc.check_totp(confirmation_code, ip):
            doc.totp_secret = None
            doc.save()
            return status_response(False, message='Некорректный код')
    slog.Log(key='', type=120002, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile).save()
    return status_response(True)


@login_required
def disable_totp(request):
    data = json.loads(request.body)
    confirmation_code = data.get('confirmationCode')
    doc: DoctorProfile = request.user.doctorprofile
    if not doc.totp_secret:
        return status_response(False, message='Двухфакторная аутентификация уже выключена')
    if not confirmation_code:
        return status_response(False, message='Некорректный код')
    ip = slog.Log.get_client_ip(request)
    if not doc.check_totp(confirmation_code, ip):
        return status_response(False, message='Некорректный код')
    with transaction.atomic():
        doc.totp_secret = None
        doc.save()
    slog.Log(key='', type=120003, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile).save()
    return status_response(True)


@login_required
def update_restricted_directions(request):
    request_data: dict = json.loads(request.body)
    user_pk: int = request_data.get('userPk')
    hospital_pk: int = request_data.get('hospitalPk')
    doctor_profile: DoctorProfile = DoctorProfile.objects.get(user_id=user_pk)
    hospital: Hospitals = Hospitals.objects.get(pk=hospital_pk)
    if hospital.is_external_performing_organization:
        price = PriceName.get_hospital_price_by_date(hospital_pk, current_time(only_date=True), current_time(only_date=True), is_subcontract=False, external_performer=True)
    else:
        price = PriceName.get_hospital_price_by_date(hospital_pk, current_time(only_date=True), current_time(only_date=True), is_subcontract=True, external_performer=False)
    price_researches_ids = PriceCoast.get_researches_ids_by_price(price.pk)
    all_researches_ids = Researches.get_all_ids()
    research_for_restrict = set(all_researches_ids - price_researches_ids)
    doctor_profile.restricted_to_direct.add(*research_for_restrict)
    doctor_profile.save()
    return status_response(True)


@login_required
def cancel_restricted_directions(request):
    request_data: dict = json.loads(request.body)
    user_pk: int = request_data.get('userPk')
    doctor_profile: DoctorProfile = DoctorProfile.objects.get(user_id=user_pk)
    doctor_profile.restricted_to_direct.clear()
    return status_response(True)


@login_required
@group_required('Статистика-реестры')
def get_doctors_by_group(request):
    result = [{"id": -1, "label": "Все"}, *[{"id": x.pk, "label": x.get_full_fio()} for x in DoctorProfile.objects.filter(user__groups__name__in=GROUP_USER_FOR_FILTER).order_by('family')]]
    return JsonResponse({"rows": result})
