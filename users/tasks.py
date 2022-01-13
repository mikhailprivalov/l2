from django.core.mail import send_mail

from laboratory.settings import EMAIL_HOST_USER
from laboratory.celery import app


@app.task(bind=True)
def send_new_password(self, email: str, username: str, password: str, organization: str):
    send_mail(
        'Новый пароль',
        f"Информационная система L2, данные для входа.\n\n"
        f"Имя пользователя: {username}\nВаш новый пароль: {password}\n\n\n{organization}",
        f"L2 <{EMAIL_HOST_USER}>",
        [email],
        fail_silently=True,
    )


@app.task(bind=True)
def send_login(self, email: str, username: str, ip: str, organization: str):
    send_mail(
        'Вход в систему',
        f"Успешная авторизация в системе L2.\n\n"
        f"Имя пользователя: {username}\nIP адрес: {ip}\n\n\n{organization}",
        f"L2 <{EMAIL_HOST_USER}>",
        [email],
        fail_silently=True,
    )
