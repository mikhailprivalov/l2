from django.db import models
from users.models import DoctorProfile
from django.utils import timezone
from utils.dates import try_strptime
import simplejson as json


class Departments(models.Model):
    title = models.CharField(max_length=255, help_text='структурное подразделение')

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Структурное подразделение'
        verbose_name_plural = 'Структурные подразделения'

    @staticmethod
    def get_all_departments():
        return {i.pk: i.title for i in Departments.objects.all()}

    @staticmethod
    def update_departmnet(data):
        if not data.get("pk") and data.get("title"):
            d = Departments(title=data["title"])
            d.save()
        elif data.get("pk") and data.get("title"):
            d = Departments.objects.get(pk=data["pk"])
            d.title = data["titel"]
            d.save()


class Persons(models.Model):
    last_name = models.CharField(max_length=255, help_text='Фамилия')
    first_name = models.CharField(max_length=255, help_text='Имя')
    patronymic = models.CharField(max_length=255, help_text='Отчество')
    snils = models.CharField(max_length=255, help_text='СНИЛС')

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic} {self.snils}"

    class Meta:
        verbose_name = 'Физлицо'
        verbose_name_plural = 'Физлица'


class TypeWorkTime(models.Model):
    title = models.CharField(max_length=255, help_text='Занятость (осн | внутр.свом| внеш. совм)')

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Тип занятости'
        verbose_name_plural = 'Типы занятости'


class Posts(models.Model):
    title = models.CharField(max_length=255, help_text='Справочник должностей')

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'

    @staticmethod
    def get_posts():
        posts = Posts.objects.all()
        result = [{
            "postPk": post.pk,
            "postTitle": post.title
        } for post in posts]

        return result

    @staticmethod
    def update_post(data):
        post = Posts.objects.get(pk=data.get("postPk", -1))
        post.title = data.get("title", "")
        post.save()
        return {"postPk": post.pk, "postTitle": post.title}


    @staticmethod
    def get_post(post_pk):
        post = Posts.objects.get(pk=post_pk)
        return {"postPk": post.pk, "postTitle": post.title}


class Employees(models.Model):
    person = models.ForeignKey(Persons, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    post = models.ForeignKey(Posts, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    type_post = models.ForeignKey(TypeWorkTime, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    department = models.ForeignKey(Departments, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    number_unit_time = models.DecimalField(max_digits=10, decimal_places=2, default=1, help_text='Кол-во единиц ставок')
    tabel_number = models.CharField(max_length=255, help_text='Табельный номер', db_index=True)

    def __str__(self):
        return f"{self.tabel_number} {self.person} {self.type_post} {self.department}"

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    @staticmethod
    def get_all_employees_by_department(depart_pk):
        employees = None
        result = []
        if depart_pk:
            employees = Employees.objects.filter(department_id=depart_pk)
        if employees:
            result = [{
                "personLastName": emp.person.last_name,
                "personFirstName": emp.person.first_name,
                "personPatronymic": emp.person.patronymic,
                "personPk": emp.person.pk,
                "personSnils": emp.person.snils,
                "tabelNumber": emp.tabel_number,
                "numberUnitTime": emp.number_unit_time,
                "typePost": emp.type_post.title,
                "typePostPk": emp.type_post.pk,
                "postPk": emp.post.pk,
                "postTitle": emp.post.title,
                "departmentPk": depart_pk,
            } for emp in employees]

        return result


    @staticmethod
    def update_employee(data):
        employee = Employees.objects.get(pk=data.get("employeePk"))
        if data.get("postId", None):
            employee.post_id = data.get("postId", None)
        if data.get("type_post", None):
            employee.type_post = data.get("type_post", None)
        if data.get("number_unit_time", None):
            employee.number_unit_time = data.get("number_unit_time", None)
        if data.get("tabel_number", None):
            employee.tabel_number = data.get("tabel_number", None)
        employee.save()

    @staticmethod
    def get_employee(employee_pk):
        emp = Employees.objects.get(pk=employee_pk)
        result = {
            "personLastName": emp.person.last_name,
            "personFirstName": emp.person.first_name,
            "personPatronymic": emp.person.patronymic,
            "personPk": emp.person.pk,
            "personSnils": emp.person.snils,
            "tabelNumber": emp.tabel_number,
            "numberUnitTime": emp.number_unit_time,
            "typePost": emp.type_post.title,
            "typePostPk": emp.type_post.pk,
            "postPk": emp.post.pk,
            "postTitle": emp.post.title,
            "departmentPk": emp.department.pk,
        }

        return result


class TabelDocuments(models.Model):
    STATUS_APPROVED = 'STATUS_APPROVED'
    STATUS_CHECK = 'STATUS_CHECK'
    STATUS_TO_CORRECT = 'STATUS_TO_CORRECT'

    STATUS_TYPES = (
        (STATUS_APPROVED, 'Утвержден'),
        (STATUS_CHECK, 'На проверке'),
        (STATUS_TO_CORRECT, 'Исправить'),
    )

    doc_confirmation = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, help_text='Профиль автора', on_delete=models.SET_NULL)
    doc_confirmation_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время подтверждения табеля')
    time_save = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время сохранения табеля')
    month_tabel = models.DateField(help_text='Месяц учета', db_index=True, default=None, blank=True, null=True)
    department = models.ForeignKey(Departments, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    is_actual = models.BooleanField(help_text="Акутальный", default=True)
    version = models.PositiveSmallIntegerField(default=None, db_index=True, blank=True, null=True)
    parent_document = models.ForeignKey('self', related_name='parent_tabel_document', help_text="Документ основание", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    comment_checking = models.TextField(blank=True, null=True, help_text="Комментарий от проверяющего")
    status = models.CharField(max_length=20, null=True, blank=True, default=None, db_index=True, choices=STATUS_TYPES, help_text="Статус")
    doc_change_status = models.ForeignKey(DoctorProfile, related_name='doc_change_status', null=True, blank=True, db_index=True, help_text='Профиль проверяющего', on_delete=models.SET_NULL)
    doc_change_status_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_change_status = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время изменения статуса')

    class Meta:
        verbose_name = 'Табель-документ'
        verbose_name_plural = 'Табель-документы'

    @staticmethod
    def create_tabel_document(data, docprofile):
        month_tabel = try_strptime(data["dateTabel"]).date()
        department_pk = data["departmentPk"]
        version = 1
        parent_document = None
        if data.get("parentDocumentPk", None):
            parent_document = TabelDocuments.objects.get(pk=data["parentDocumentPk"])
            version = parent_document.version + 1

        td = TabelDocuments(
            doc_confirmation=docprofile,
            doc_confirmation_string=docprofile.get_full_fio(),
            time_save=timezone.now(),
            month_tabel=month_tabel,
            department_id=department_pk,
            is_actual=True,
            parent_document_id=data.get("parentDocumentPk", None),
            version=version
        ).save()
        if data.get("withConfirm", None):
            td.time_confirmation = timezone.now()
            td.status = "STATUS_CHECK"
            if parent_document:
                parent_document.is_actual = False
                parent_document.save()

        td.save()

    @staticmethod
    def change_status_tabel_document(tabel_pk, data, docprofile):
        td = TabelDocuments.objects.get(pk=tabel_pk)
        td.doc_change_status = docprofile
        td.doc_change_status_string = docprofile.get_full_fio()
        td.time_change_status = timezone.now()
        td.comment_checking = data.get("commentChecking", "")
        td.status = data.get("status", "")
        td.save()


class FactTimeWork(models.Model):
    STATUS_WORK = 'STATUS_WORK'
    STATUS_HOLIDAY = 'STATUS_HOLIDAY'
    STATUS_SICK = 'STATUS_HOLIDAY'
    STATUS_BUSINESS_TRIP = 'STATUS_BUSINESS_TRIP'
    STATUS_DISMISS = 'STATUS_DISMISS'

    STATUS_TYPES = (
        (STATUS_WORK, 'Работа'),
        (STATUS_HOLIDAY, 'Отпуск'),
        (STATUS_HOLIDAY, 'Больничный'),
        (STATUS_BUSINESS_TRIP, 'Командировка'),
        (STATUS_DISMISS, 'Уволен'),
    )

    tabel_document = models.ForeignKey(TabelDocuments, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    employee = models.ForeignKey(Employees, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    date = models.DateField(help_text='Дата учета', db_index=True, default=None, blank=True, null=True)
    night_hours = models.DecimalField(max_digits=10, decimal_places=2)
    common_hours = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, null=True, blank=True, default=None, db_index=True, choices=STATUS_TYPES, help_text="Статус")

    class Meta:
        verbose_name = 'Табель времени - акутальный'
        verbose_name_plural = 'Табели времени (актуальные данные)'


class DocumentFactTimeWork(models.Model):
    """
    data_document = {"tabelDocumentPk": "", "personData": [
                            {
                                "snils": "121212121",
                                "personLastname": "sds",
                                "personFirstName": "sds",
                                "personPatronymic": "sds",
                                "employeeData": [
                                    {
                                        "postTitle": "postTitle",
                                        "typePost": "typePost",
                                        "departmentTitle": "departmentTitle",
                                        "tabelNumber": "tabelNumber",
                                        "dates": ["все даты месяца ч/з запятую"],
                                        "nightHours": {"дата": "значение", "дата1": "значение", "дат2": "значение"},
                                        "commonHours": {}
                                    },
                                ]
                            },
                        ]
                    }
    """
    tabel_document = models.ForeignKey(TabelDocuments, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    data_document = models.TextField(blank=True, null=True, help_text="Данные документа")

    class Meta:
        verbose_name = 'Табель документ'
        verbose_name_plural = 'Табель документы'

    @staticmethod
    def save_fact_time_work_document(tabel_pk, data_document):
        if tabel_pk > -1:
            document_fact_time = DocumentFactTimeWork.objects.get(pk=tabel_pk)
            document_fact_time.data_document = data_document
            document_fact_time.save()

    @staticmethod
    def get_fact_time_work_document(tabel_pk):
        data = ""
        if tabel_pk > -1:
            document_fact_time = DocumentFactTimeWork.objects.get(pk=tabel_pk)
            data = json.loads(document_fact_time)
            for person in data.get("personData") or []:
                for employeee in person.get("employeeData") or []:
                    tmp_dates = sorted(employeee.get("dates", []).copy())
                    tmp_night_hours_dates = ['' for i in range(len(tmp_dates))]
                    tmp_night_hours = employeee.get("nightHours", {})
                    tmp_common_hours = employeee.get("commonHours", {})



        return data


class Holidays(models.Model):
    year = models.SmallIntegerField(blank=True, default=None, null=True)
    day = models.DateField()

    def __str__(self):
        return f"{self.year} {self.day}"

    class Meta:
        verbose_name = 'Праздничный день'
        verbose_name_plural = 'Праздничные дни'
