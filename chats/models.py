import datetime
import os
import uuid

import hashlib
from PIL import Image
from django.db import models, transaction
from django.db.models import Q
from django.core.cache import cache

from users.models import DoctorProfile


class Dialog(models.Model):
    doctor1 = models.ForeignKey('users.DoctorProfile', on_delete=models.CASCADE, related_name='chat_doctor1', db_index=True)
    doctor2 = models.ForeignKey('users.DoctorProfile', on_delete=models.CASCADE, related_name='chat_doctor2', db_index=True, null=True, blank=True)  # null если сообщение от системы
    unread_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('doctor1', 'doctor2')
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'

    def __str__(self):
        return f'{self.doctor1} - {self.doctor2}'

    @staticmethod
    def add_message_text(dialog, author, text):
        return Dialog.add_message(dialog, author, text=text)

    @staticmethod
    def add_message_image(dialog, author, image):
        return Dialog.add_message(dialog, author, image=image)

    @staticmethod
    def add_message_file(dialog, author, file):
        return Dialog.add_message(dialog, author, file=file)

    @staticmethod
    def add_message(dialog, author, text=None, image=None, file=None):
        message_type = Message.MESSAGE_TYPE_TEXT
        if image:
            message_type = Message.MESSAGE_TYPE_IMAGE
        elif file:
            message_type = Message.MESSAGE_TYPE_FILE
        with transaction.atomic():
            if image or file:
                file_to_save = image or file
                file_hash = hashlib.sha256(f"{hashlib.sha256(file_to_save.read()).hexdigest()}-{file_to_save.name}".encode()).hexdigest()
                file_to_save.seek(0)
                message = Message.objects.filter(file_hash=file_hash).first()
                if message and message.file:
                    file_to_save = message.file
            else:
                file_hash = None
                file_to_save = None
            message = Message.objects.create(
                dialog=dialog,
                author=author,
                text=text or '',
                file=file_to_save,
                file_hash=file_hash,
                type=message_type
            )
            dialog = Dialog.objects.select_for_update().get(pk=dialog.pk)
            dialog.unread_count += 1
            dialog.save(update_fields=['unread_count'])
            doctor1 = DoctorProfile.objects.select_for_update().get(pk=dialog.doctor1.pk)
            doctor1.inc_messages_count()
            if dialog.doctor2 and dialog.doctor2 != doctor1:
                doctor2 = DoctorProfile.objects.select_for_update().get(pk=dialog.doctor2.pk)
                doctor2.inc_messages_count()
            return message

    def get_other_doctor(self, doctor):
        if self.doctor1 == doctor:
            return self.doctor2
        return self.doctor1

    def mark_as_read_for_not_author(self, doctor):
        self.chat_messages.filter(~Q(author=doctor)).update(is_read=True)

    @staticmethod
    def get_dialog_or_create(doctor1, doctor2):
        dialog1 = Dialog.objects.filter(doctor1=doctor1, doctor2=doctor2).first()
        dialog2 = Dialog.objects.filter(doctor1=doctor2, doctor2=doctor1).first()
        if dialog1 and dialog2 and dialog1 == dialog2:
            return dialog1
        if dialog1 and dialog2:
            if dialog1.chat_messages.count() > dialog2.chat_messages.count():
                dialog2.delete()
                return dialog1
            else:
                dialog1.delete()
                return dialog2
        if dialog1:
            return dialog1
        if dialog2:
            return dialog2
        dialog = Dialog.objects.create(doctor1=doctor1, doctor2=doctor2)
        return dialog

    @staticmethod
    def get_unread_messages_count(doctor):
        return Message.objects.filter(Q(dialog__doctor1=doctor) | Q(dialog__doctor2=doctor), is_read=False).exclude(author=doctor).count()

    @staticmethod
    def get_dialogs_count_key(doctor):
        return f'chats:dialogs_count:{doctor.pk}'

    @staticmethod
    def get_unread_messages_count_for_doctor_by_dialogs(doctor):
        dialogs = {}
        for dialog in Dialog.objects.filter(Q(doctor1=doctor) | Q(doctor2=doctor)).prefetch_related('chat_messages'):
            cnt = dialog.chat_messages.filter(is_read=False).exclude(author=doctor).count()
            other_doctor = dialog.get_other_doctor(doctor)
            if cnt:
                dialogs[other_doctor.pk] = cnt
        return dialogs

    def get_messages(self, last_message_id, limit):
        if last_message_id == -1:
            messages = self.chat_messages.order_by('-pk')[:limit]
        else:
            messages = self.chat_messages.filter(pk__lt=last_message_id).order_by('-pk')[:limit]
        return messages

    def get_messages_feature(self, last_message_id):
        return self.chat_messages.filter(pk__gt=last_message_id).order_by('pk')

    def get_doctor_writing_key(self, doctor):
        return f'chats:writing:{self.pk}:{doctor.pk}'

    def get_doctor_writing(self, doctor):
        return bool(cache.get(self.get_doctor_writing_key(doctor)))

    def set_doctor_writing(self, doctor):
        cache.set(self.get_doctor_writing_key(doctor), True, timeout=2)

    def delete_doctor_writing(self, doctor):
        cache.delete(self.get_doctor_writing_key(doctor))


def get_chats_message_upload_path(instance, filename):
    date_tuple_yyyy_mm_dd = [str(x) for x in datetime.datetime.now().timetuple()[:3]]
    return os.path.join('chats', *date_tuple_yyyy_mm_dd, str(uuid.uuid4()), filename)


def get_image_dimensions(image):
    img = Image.open(image)
    size = {
        'width': img.width,
        'height': img.height,
    }

    img.close()

    return size


class Message(models.Model):
    MESSAGE_TYPE_TEXT = 1
    MESSAGE_TYPE_FILE = 2
    MESSAGE_TYPE_IMAGE = 3

    MESSAGE_TYPE_CHOICES = (
        (MESSAGE_TYPE_TEXT, 'Текст'),
        (MESSAGE_TYPE_FILE, 'Файл'),
        (MESSAGE_TYPE_IMAGE, 'Изображение'),
    )

    dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE, related_name='chat_messages', db_index=True)
    author = models.ForeignKey('users.DoctorProfile', on_delete=models.CASCADE, related_name='chat_messages', db_index=True)
    text = models.TextField()
    type = models.IntegerField(choices=MESSAGE_TYPE_CHOICES, default=MESSAGE_TYPE_TEXT)
    file = models.FileField(upload_to=get_chats_message_upload_path, null=True, blank=True)
    file_hash = models.CharField(max_length=64, null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    image_width = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return f'{self.dialog} - {self.author} - {self.text}'

    def get_file_name(self):
        if not self.file:
            return ''
        return os.path.basename(self.file.name)

    def get_image_dimensions(self):
        if not self.file or self.type != self.MESSAGE_TYPE_IMAGE:
            return None

        if self.image_width and self.image_height:
            return {
                'width': self.image_width,
                'height': self.image_height,
            }

        try:
            sizes = get_image_dimensions(self.file)
            self.image_width = sizes['width']
            self.image_height = sizes['height']
            self.save()
            return sizes
        except Exception:
            return {
                'width': 0,
                'height': 0,
            }

    def message_json(self):
        return {
            'id': self.pk,
            'dialogId': self.dialog.pk,
            'author': self.author.pk,
            'authorName': self.author.get_fio(),
            'text': self.text if self.type == self.MESSAGE_TYPE_TEXT else f"{self.get_type_display()}: {self.get_file_name()}",
            'type': self.type,
            'file': {
                "url": self.file.url,
                "name": self.get_file_name(),
            } if self.file else None,
            'imageDimensions': self.get_image_dimensions(),
            'time': int(self.created_at.timestamp()),
            'read': self.is_read,
        }
