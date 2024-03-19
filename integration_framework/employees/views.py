import simplejson as json
from rest_framework.response import Response

from hospitals.models import Hospitals
from rest_framework.decorators import api_view
from employees import models as employees


@api_view()
def cash_register(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    register_date = body.get("cashRegisterDate")
    data = body.get("data")

    for i in data:
        current_employee = i.get("employee")
        tabel_number = current_employee.get("tabelNumber")
        current_department = i.get("office")
        if not employees.Department.objects.filter(external_id=current_department.get("id")).first():
            department = employees.Department(name=current_department.get("title"), external_id=current_department.get("id"))
            department.save()
        else:
            department = employees.Department.objects.filter(external_id=current_department.get("id")).first()

        hospital = Hospitals.get_default_hospital()
        if not employees.EmployeePosition.objects.filter(tabel_number=tabel_number).first():
            new_employee = employees.Employee(
                family=current_employee.get("lastName"),
                name=current_employee.get("firstName"),
                patronymic=current_employee.get("patronymic"),
                hospital=hospital
            )
            new_employee.save()
        else:
            new_employee = employees.EmployeePosition.objects.filter(tabel_number=tabel_number).first()
        current_money = i.get("money")
        employees.CashRegister(
            employee_position=new_employee,
            department=department,
            day=register_date,
            received_terminal=current_money.get("received_terminal", 0),
            received_cash=current_money.get("received_cash", 0),
            return_terminal=current_money.get("return_terminal", 0),
            return_cash=current_money.get("return_cash", 0)
        )
    return Response({"ok": True})


@api_view()
def get_register_data(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")
    type_period = body.get("typePeriod")
    mode = body.get("mode")
    if mode == "department":
        if type_period == "month":
            pass
        elif type_period == "day":
            pass

    elif mode == "person":
        pass

    return Response({"ok": True})