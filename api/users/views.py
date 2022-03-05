from django.contrib.auth.decorators import login_required
import simplejson as json
import re
from random import randint

from django.contrib.auth import authenticate, login

from laboratory.utils import current_time
from users.tasks import send_password_reset_code

from utils.response import status_response
import slog.models as slog
from users.models import DoctorProfile


def auth(request):
    data = json.loads(request.body)
    username = data.get('username', '')
    password = data.get('password', '')
    user = authenticate(username=username, password=password)
    f1 = re.findall(r"^([ X0-9]{5})([0-9a-fA-F]{5})$", username)
    if user:
        if user.is_active:
            login(request, user)
            log = slog.Log(key="", type=18, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile)
            log.save()
            request.user.doctorprofile.register_login(slog.Log.get_client_ip(request))
            return status_response(True, data={'fio': user.doctorprofile.get_full_fio()})

        return status_response(False, message="Ваш аккаунт отключен")
    elif len(password) == 0 and len(f1) == 1 and len(f1[0]) == 2:
        did = int(f1[0][0].replace("X", ""))
        u = DoctorProfile.objects.filter(pk=did).first()
        if u and u.get_login_id() == username and u.user.is_active:
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
            send_password_reset_code.delay(
                email,
                request.session['code'],
                doc.hospital_safe_title
            )
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
            slog.Log(key=new_email, type=120001, body=json.dumps({
                "ip": slog.Log.get_client_ip(request),
                "old": old_email,
                "new": new_email,
            }), user=request.user.doctorprofile).save()
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
