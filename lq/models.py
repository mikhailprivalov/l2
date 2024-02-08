from django.db import models
from django.utils import timezone

from users.models import DoctorProfile


class WindowL2(models.Model):
    title = models.CharField(max_length=511, unique=True, help_text='Наименование экрана для очередей', db_index=True)
    active_status = models.BooleanField(default=True, help_text='Статус активности', db_index=True)

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        verbose_name = 'Экран'
        verbose_name_plural = 'Экраны'


class ResourceL2(models.Model):
    title = models.CharField(max_length=511, unique=True, help_text='Наименование ресурса-очереди', db_index=True)
    short_title = models.CharField(max_length=255, default='', help_text='Короткое наименование очереди', db_index=True)
    windows_obj = models.ForeignKey(WindowL2, blank=False, null=False, db_index=True, on_delete=models.CASCADE)
    letter = models.CharField(max_length=511, help_text='Буквы для счетчика, через запятую', db_index=True)
    max_number = models.SmallIntegerField(default=0, help_text='Максимальное число для буквы')
    disable = models.BooleanField(default=False, blank=True, help_text='Отключить очередь?')

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        verbose_name = 'Очередь'
        verbose_name_plural = 'Очереди'

    def get_letter(self):
        return (self.letter, self.max_number)


class VoiceDo(models.Model):
    title = models.CharField(max_length=511, unique=True, help_text='Ресурс озвучки для очередей', db_index=True)
    resource = models.ManyToManyField(ResourceL2, help_text='Очередь')

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        verbose_name = 'Звуковой ресурс'
        verbose_name_plural = 'Звуковые ресурсы'


class StatusQueueL2(models.Model):
    STATUS_GET = 0
    STATUS_USED = 1
    STATUS_NOW = 2

    STATUS_TALON = (
        (STATUS_GET, "Получен пациентом"),
        (STATUS_USED, "Вызван"),
        (STATUS_NOW, "Озвучить"),
    )

    queue_l2 = models.ForeignKey(ResourceL2, on_delete=models.DO_NOTHING, db_index=True)
    talon_letter = models.CharField(max_length=511, help_text='Наименование ресурса', db_index=True)
    talon_number = models.SmallIntegerField(help_text='Наименование ресурса', db_index=True)
    date_get = models.DateTimeField(default=timezone.now, null=True, blank=True, help_text='Время взятия талона пациентом')
    date_invite = models.DateTimeField(default=None, null=True, blank=True, help_text='Время приглашения')
    status = models.IntegerField(choices=STATUS_TALON, default=STATUS_GET, blank=True, help_text="Статус талона")
    doc_invite = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_invite", help_text='Кто пригласил', on_delete=models.SET_NULL)

    def __str__(self):
        return "{}".format(self.queue_l2)

    class Meta:
        verbose_name = 'Талон'
        verbose_name_plural = 'Талоны всех очередей'

    @staticmethod
    def next_talon_num(queue_resource):
        obj_resource = ResourceL2.objects.filter(pk=queue_resource).first()
        let_num = obj_resource.get_letter()
        last_talon = StatusQueueL2.objects.values_list('talon_letter', 'talon_number').filter(queue_l2=obj_resource).order_by("-date_get").first()
        print(last_talon)  # noqa: T001
        num_last = 0
        let_last = ''
        if last_talon:
            let_last = last_talon[0]
            num_last = last_talon[1]

        let_list = let_num[0].split(',')
        if num_last == let_num[1]:
            n = 1
            if let_last == let_list[-1]:
                ll = let_list[0]
            else:
                index = let_list.index(let_last)
                ll = let_list[index + 1]
        else:
            n = num_last + 1
            ll = let_last

        return ll, n
