import simplejson as json
from rest_framework.response import Response

from hospitals.models import Hospitals
from rest_framework.decorators import api_view
from employees import models as employees


@api_view(["GET", "POST"])
def cash_register(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    register_date = body.get("cashRegisterDate")
    print(register_date)
    data = body.get("data")
    hospital = Hospitals.get_default_hospital()
    for i in data:
        current_employee = i.get("employee")
        tabel_number = current_employee.get("tabelNumber")
        current_department = i.get("office")
        if not employees.Department.objects.filter(external_id=current_department.get("id")).first():
            department = employees.Department(hospital=hospital, name=current_department.get("title"), external_id=current_department.get("id"))
            department.save()
        else:
            department = employees.Department.objects.filter(external_id=current_department.get("id")).first()

        if not employees.EmployeePosition.objects.filter(tabel_number=tabel_number).first():
            employee_person = employees.Employee(
                family=current_employee.get("lastName"), name=current_employee.get("firstName"), patronymic=current_employee.get("patronymic"), hospital=hospital
            )
            employee_person.save()

            position_id = current_employee.get("positionId")
            if employees.Position.objects.filter(hospital=hospital, external_id=position_id).first():
                position = employees.Position.objects.filter(hospital=hospital, external_id=position_id).first()
            else:
                position = employees.Position(hospital=hospital, external_id=position_id, name=current_employee.get("positionTitle"))
                position.save()
            new_employee = employees.EmployeePosition(position=position, employee=employee_person, department=department, rate=1.0, tabel_number=tabel_number)
            new_employee.save()
        else:
            new_employee = employees.EmployeePosition.objects.filter(tabel_number=tabel_number).first()

        current_money = i.get("money")
        cash_register = employees.CashRegister.objects.filter(employee_position=new_employee, accounting_day=register_date).first()
        if cash_register:
            cash_register.received_terminal = current_money.get("receivedTerminal", 0)
            cash_register.received_cash = current_money.get("receivedСash", 0)
            cash_register.return_terminal = current_money.get("returnTerminal", 0)
            cash_register.return_cash = current_money.get("returnCash", 0)
        else:
            cash_register = employees.CashRegister(
                employee_position=new_employee,
                department=department,
                accounting_day=register_date,
                received_terminal=current_money.get("receivedTerminal", 0),
                received_cash=current_money.get("receivedСash", 0),
                return_terminal=current_money.get("returnTerminal", 0),
                return_cash=current_money.get("returnCash", 0),
            )
        cash_register.save()
    return Response({"ok": True})
