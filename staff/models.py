from django.db import models


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
        result = [{"postPk": post.pk, "postTitle": post.title} for post in posts]

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


class Holidays(models.Model):
    year = models.SmallIntegerField(blank=True, default=None, null=True)
    day = models.DateField()

    def __str__(self):
        return f"{self.year} {self.day}"

    class Meta:
        verbose_name = 'Праздничный день'
        verbose_name_plural = 'Праздничные дни'
