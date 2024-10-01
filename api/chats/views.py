import json
from typing import List

from PIL import Image
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse

from chats.models import Dialog, Message
from users.models import DoctorProfile
from utils.response import status_response


@login_required
def mark_as_online_user(request):
    if hasattr(request.user, 'doctorprofile') and request.user.doctorprofile:
        request.user.doctorprofile.mark_as_online()

    return JsonResponse({"status": "ok"})


@login_required
def mark_as_offline_user(request):
    if hasattr(request.user, 'doctorprofile') and request.user.doctorprofile:
        request.user.doctorprofile.mark_as_offline()

    return JsonResponse({"status": "ok"})


@login_required
def get_users_for_hospital(request):
    request.user.doctorprofile.mark_as_online()
    hospital = request.user.doctorprofile.get_hospital()

    cache_key = f"chats:users-by-departments:{hospital.pk}"
    departments = cache.get(cache_key)
    if not departments:
        doctorprofiles: List[DoctorProfile] = hospital.doctorprofile_set.filter(
            hospital=hospital,
            user__is_active=True,
            dismissed=False,
        ).select_related("podrazdeleniye", "position", "specialities")

        departments = {}
        for doctorprofile in doctorprofiles:
            department = doctorprofile.podrazdeleniye

            if department:
                department_id = department.pk
                department_title = department.get_title()
            else:
                department_id = -1
                department_title = "Без отделения"

            if department_id not in departments:
                departments[department_id] = {
                    "id": department_id,
                    "title": department_title,
                    "usersOnline": 0,
                    "users": [],
                }

            dialog_data = doctorprofile.get_dialog_data()

            departments[department_id]["users"].append(dialog_data)

            if dialog_data["isOnline"]:
                departments[department_id]["usersOnline"] += 1

        for department in departments.values():
            department["users"].sort(key=lambda x: x["name"])
            department["users"].sort(key=lambda x: x["isOnline"], reverse=True)

        departments = list(departments.values())
        departments.sort(key=lambda x: x["title"])

        cache.set(cache_key, departments, 90)

    return JsonResponse({"departments": departments})


@login_required
def get_messages_count(request):
    request_data = json.loads(request.body)
    doctor = request.user.doctorprofile
    unread_messages_count = Dialog.get_unread_messages_count(doctor)
    prev_unread_messages_count_key = f"chats:unread-messages-count:{doctor.pk}"
    prev_unread_messages_count = int(cache.get(prev_unread_messages_count_key) or 0)
    unread_dialogs_key = f"chats:unread-dialogs:{doctor.pk}"
    unread_dialogs = cache.get(unread_dialogs_key)

    if prev_unread_messages_count != unread_messages_count or unread_dialogs is None:
        cache.set(prev_unread_messages_count_key, unread_messages_count)
        unread_dialogs = Dialog.get_unread_messages_count_for_doctor_by_dialogs(doctor)
        cache.set(unread_dialogs_key, unread_dialogs)

    total_messages_count = doctor.get_messages_count()

    notifications = []
    notify_token = request_data.get("notifyToken")
    if notify_token:
        messages = doctor.get_messages_from_queue_by_token(notify_token)
        if messages:
            notifications = [message.message_json() for message in Message.objects.filter(pk__in=messages)]

    new_token = doctor.check_or_make_new_notify_queue_token(notify_token)

    return JsonResponse(
        {"unreadMessages": unread_messages_count, "totalMessages": total_messages_count, "unreadDialogs": unread_dialogs, "notifications": notifications, "newToken": new_token}
    )


@login_required
def get_dialog_pk(request):
    request_data = json.loads(request.body)
    doctor1 = request.user.doctorprofile
    doctor_pk = request_data.get("userId")
    doctor2 = DoctorProfile.objects.get(pk=doctor_pk)

    if doctor2.get_hospital() != doctor1.get_hospital():
        return status_response(False, 'Forbidden')

    dialog = Dialog.get_dialog_or_create(doctor1, doctor2)

    return JsonResponse({"dialogId": dialog.pk})


@login_required
def get_dialog_data(request):
    request_data = json.loads(request.body)
    dialog_pk = request_data.get("dialogId")
    dialog = Dialog.objects.get(pk=dialog_pk)

    if request.user.doctorprofile != dialog.doctor1 and request.user.doctorprofile != dialog.doctor2:
        return status_response(False, "Forbidden")

    other_doctor = dialog.get_other_doctor(request.user.doctorprofile)

    return JsonResponse(
        {
            "user": other_doctor.get_dialog_data(),
            "totalMessages": dialog.chat_messages.count(),
        }
    )


@login_required
def send_message(request):
    file = request.FILES.get('file')
    image = request.FILES.get('image')
    form = request.FILES['form'].read()
    request_data = json.loads(form)
    dialog_pk = request_data.get("dialogId")
    dialog = Dialog.objects.get(pk=dialog_pk)

    if request.user.doctorprofile != dialog.doctor1 and request.user.doctorprofile != dialog.doctor2:
        return status_response(False, "Forbidden")

    dialog.delete_doctor_writing(request.user.doctorprofile)

    message = request_data.get("text")

    message_obj = None
    if message:
        message = message[:500]
        message_obj = Dialog.add_message_text(dialog, request.user.doctorprofile, message)
    elif image:
        if image.size > 2 * 1024 * 1024:
            return status_response(False, "Image is too big")
        # check image is valid
        try:
            img = Image.open(image)
            img.verify()
            img.close()
        except Exception:
            return status_response(False, "Image is invalid")
        message_obj = Dialog.add_message_image(dialog, request.user.doctorprofile, image)
    elif file:
        if file.size > 2 * 1024 * 1024:
            return status_response(False, "File is too big")
        message_obj = Dialog.add_message_file(dialog, request.user.doctorprofile, file)

    if message_obj:
        doctor2 = dialog.get_other_doctor(request.user.doctorprofile)
        if doctor2 != request.user.doctorprofile:
            doctor2.add_message_id_to_queues(message_obj.pk)

        return status_response(True, data={"message": message_obj.message_json()})
    return status_response(False, "Message is empty")


@login_required
def get_notify_token(request):
    doctor: DoctorProfile = request.user.doctorprofile
    token = doctor.create_notify_queue_token()

    return JsonResponse({"notifyToken": token})


@login_required
def get_messages(request):
    request_data = json.loads(request.body)
    dialog_pk = request_data.get("dialogId")
    last_message_id = request_data.get("lastMessageId")
    limit = 20
    dialog = Dialog.objects.get(pk=dialog_pk)

    if request.user.doctorprofile != dialog.doctor1 and request.user.doctorprofile != dialog.doctor2:
        return status_response(False, "Forbidden")

    messages = dialog.get_messages(last_message_id, limit)

    Message.objects.filter(pk__in=[x.pk for x in messages], is_read=False).exclude(author=request.user.doctorprofile).update(is_read=True)

    messages = list(messages)
    messages.reverse()

    return JsonResponse({"messages": [message.message_json() for message in messages]})


@login_required
def get_messages_feature(request):
    request_data = json.loads(request.body)
    dialog_pk = request_data.get("dialogId")
    dialog = Dialog.objects.get(pk=dialog_pk)

    if request.user.doctorprofile != dialog.doctor1 and request.user.doctorprofile != dialog.doctor2:
        return status_response(False, "Forbidden")

    last_message_id = request_data.get("lastMessageId")
    messages = dialog.get_messages_feature(last_message_id)

    Message.objects.filter(pk__in=[x.pk for x in messages], is_read=False).exclude(author=request.user.doctorprofile).update(is_read=True)

    return JsonResponse({"messages": [message.message_json() for message in messages]})


@login_required
def read_messages(request):
    request_data = json.loads(request.body)
    dialog_pk = request_data.get("dialogId")
    dialog = Dialog.objects.get(pk=dialog_pk)

    if request.user.doctorprofile != dialog.doctor1 and request.user.doctorprofile != dialog.doctor2:
        return status_response(False, "Forbidden")

    message_ids = request_data.get("messageIds")

    for message_id in message_ids:
        message = Message.objects.get(pk=message_id)

        if message.dialog != dialog:
            return status_response(False, "Forbidden")

        message.is_read = True
        message.save()

    return status_response(True)


@login_required
def get_read_statuses(request):
    request_data = json.loads(request.body)
    dialog_pk = request_data.get("dialogId")
    dialog = Dialog.objects.get(pk=dialog_pk)

    if request.user.doctorprofile != dialog.doctor1 and request.user.doctorprofile != dialog.doctor2:
        return status_response(False, "Forbidden")

    message_ids = request_data.get("messageIds")

    if message_ids:
        messages = Message.objects.filter(pk__in=message_ids, is_read=True, dialog=dialog).values_list("pk", flat=True)
    else:
        messages = []

    if dialog.doctor1 != dialog.doctor2:
        other_doctor = dialog.get_other_doctor(request.user.doctorprofile)
        is_writing = dialog.get_doctor_writing(other_doctor)
    else:
        is_writing = False

    return JsonResponse({"statuses": list(messages), "isWriting": is_writing})


@login_required
def update_is_writing(request):
    request_data = json.loads(request.body)
    dialog_pk = request_data.get("dialogId")
    dialog = Dialog.objects.get(pk=dialog_pk)

    if request.user.doctorprofile != dialog.doctor1 and request.user.doctorprofile != dialog.doctor2:
        return status_response(False, "Forbidden")

    if dialog.doctor1 != dialog.doctor2:
        dialog.set_doctor_writing(request.user.doctorprofile)

    return status_response(True)
