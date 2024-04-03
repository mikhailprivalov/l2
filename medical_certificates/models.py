from django.db import models
from directory.models import Researches


class MedicalCertificates(models.Model):
    """
    Виды справок
    """

    CERTIFICATE_FORMS = (
        (38001, '38001. В бассейн '),
        (38002, '38002. Нарколог-психиатр'),
        (38003, '38003. О проведенном приеме'),
        (38004, '38004. Заключение профпатолога'),
        (38005, '38005. Роспотребнадзор'),
        (38006, '38006. Для эпидемиолога'),
        (38007, '38007. 001-ГС/у'),
        (38008, '38008. 086-1/у (Судья)'),
        (38009, '38009. Прикреплен'),
        (38010, '38010. 086/у'),
        (38011, '38011. Справка профпатолога'),
        (38012, '38012. Заключение 27Н'),
        (38013, '38013. Заключение 27Н-v2'),
    )

    title = models.CharField(max_length=63, help_text='Название справки')
    certificate_form = models.IntegerField(default=0, blank=True, choices=CERTIFICATE_FORMS, help_text="Форма результат")
    general = models.BooleanField(default=False, blank=True, help_text='Общие справки для всех', db_index=True)

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = 'Справка'
        verbose_name_plural = 'Справки медицинские(виды)'


class ResearchesCertificate(models.Model):
    """
    Справки для определенных услуг
    """

    research = models.ForeignKey(Researches, null=True, blank=True, help_text='Вид исследования из справочника', db_index=True, on_delete=models.CASCADE)
    medical_certificate = models.ForeignKey(MedicalCertificates, null=True, blank=True, help_text='Вид справки', db_index=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("research", "medical_certificate")
        verbose_name = 'справка для услуг'
        verbose_name_plural = 'Справки-услуги'
