import os
import uuid

from django.db import models
from django.db.models import Q


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
        message = Message.objects.create(dialog=dialog, author=author, text=text)
        dialog.unread_count += 1
        dialog.save(update_fields=['unread_count'])
        dialog.doctor1.inc_messages_count()
        if dialog.doctor2:
            dialog.doctor2.inc_messages_count()
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
            if cnt:
                dialogs[dialog.pk] = cnt
        return dialogs

    def get_messages(self, last_message_id, limit):
        if last_message_id == -1:
            messages = self.chat_messages.order_by('-pk')[:limit]
        else:
            messages = self.chat_messages.filter(pk__lt=last_message_id).order_by('-pk')[:limit]
        return messages

    def get_messages_feature(self, last_message_id):
        return self.chat_messages.filter(pk__gt=last_message_id).order_by('pk')


def get_chats_message_upload_path(instance, filename):
    return os.path.join('doc_call_uploads', str(instance.dialog.pk), str(uuid.uuid4()), filename)


class Message(models.Model):
    MESSAGE_TYPE_TEXT = 1
    MESSAGE_TYPE_FILE = 2
    MESSAGE_TYPE_CARD = 3
    MESSAGE_TYPE_DIRECTION = 4
    MESSAGE_TYPE_RESULT = 5

    MESSAGE_TYPE_CHOICES = (
        (MESSAGE_TYPE_TEXT, 'Текст'),
        (MESSAGE_TYPE_FILE, 'Файл'),
        (MESSAGE_TYPE_CARD, 'Карта пациента'),
        (MESSAGE_TYPE_DIRECTION, 'Направление'),
        (MESSAGE_TYPE_RESULT, 'Результат'),
    )

    dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE, related_name='chat_messages', db_index=True)
    author = models.ForeignKey('users.DoctorProfile', on_delete=models.CASCADE, related_name='chat_messages', db_index=True)
    text = models.TextField()
    type = models.IntegerField(choices=MESSAGE_TYPE_CHOICES, default=MESSAGE_TYPE_TEXT)
    file = models.FileField(upload_to=get_chats_message_upload_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return f'{self.dialog} - {self.author} - {self.text}'

    def message_json(self):
        return {
            'id': self.pk,
            'dialogId': self.dialog.pk,
            'author': self.author.pk,
            'authorName': self.author.get_fio(),
            'text': self.text,
            'type': self.type,
            'file': self.file.url if self.file else None,
            'time': int(self.created_at.timestamp()),
            'read': self.is_read,
        }
