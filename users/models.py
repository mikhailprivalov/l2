from django.db import models
from django.contrib.auth.models import User
from podrazdeleniya.models import Podrazdeleniya


class DoctorProfile(models.Model):
    """
    Профили врачей
    """
    labtypes = (
        (0, "Не из лаборатории"),
        (1, "Врач"),
        (2, "Лаборант"),
    )
    user = models.OneToOneField(User, null=True, blank=True, help_text='Ссылка на Django-аккаунт')
    fio = models.CharField(max_length=255, help_text='ФИО')
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True, help_text='Подразделение', db_index=True)
    isLDAP_user = models.BooleanField(default=False,
                                      blank=True,
                                      help_text='Флаг, показывающий, что это импортированый из LDAP пользователь')
    labtype = models.IntegerField(choices=labtypes, default=0, blank=True,
                                  help_text='Категория профиля для лаборатории')

    def get_fio(self, dots=True):
        """
        Функция формирования фамилии и инициалов (Иванов И.И.)
        :param dots:
        :return:
        """
        fio = self.fio.strip().replace("  ", " ").strip()
        fio_split = fio.split(" ")

        if len(fio_split) == 0:
            return self.user.username
        if len(fio_split) == 1:
            return fio

        if len(fio_split) > 3:
            fio_split = [fio_split[0], " ".join(fio_split[1:-2]), fio_split[-1]]

        if dots:
            return fio_split[0] + " " + fio_split[1][0] + "." + ("" if len(fio_split) == 2 else fio_split[2][0] + ".")
        return fio_split[0] + " " + fio_split[1][0] + ("" if len(fio_split) == 2 else fio_split[2][0])

    def is_member(self, groups: list) -> bool:
        """
        Проверка вхождения пользователя в группу
        :param groups: названия групп
        :return: bool, входит ли в указаную группу
        """
        return self.user.groups.filter(name__in=groups).exists()

    def __str__(self):  # Получение фио при конвертации объекта DoctorProfile в строку
        if self.podrazdeleniye:
            return self.fio + ', ' + self.podrazdeleniye.title
        else:
            return self.fio

    class Meta:
        verbose_name = 'Профиль пользователя L2'
        verbose_name_plural = 'Профили пользователей L2'


class AssignmentTemplates(models.Model):
    title = models.CharField(max_length=40)
    doc = models.ForeignKey(DoctorProfile, null=True, blank=True)
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True, related_name='podr')

    def __str__(self):
        return (self.title + " | Шаблон для ") + (("всех" if self.podrazdeleniye is None else str(self.podrazdeleniye)) if self.doc is None else str(self.doc))

    class Meta:
        verbose_name = 'Шаблон назначений'
        verbose_name_plural = 'Шаблоны назначений'


class AssignmentResearches(models.Model):
    template = models.ForeignKey(AssignmentTemplates)
    research = models.ForeignKey('directory.Researches')

    def __str__(self):
        return str(self.template) + "  | " + str(self.research)

    class Meta:
        verbose_name = 'Исследование для шаблона назначений'
        verbose_name_plural = 'Исследования для шаблонов назначений'
