import simplejson as json
from rest_framework.response import Response

from hospitals.models import Hospitals
from rest_framework.decorators import api_view
from employees import models as employees
from integration_framework.employees.sql_func import get_cash_resister_by_depatment_period
import calendar


@api_view(["GET", "POST"])
def cash_register(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    register_date = body.get("cashRegisterDate")
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


@api_view(["GET", "POST"])
def get_register_data(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    mode = body.get("mode")
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")

    date_start_year = date_start[:4]
    date_start_month = date_start[4:6]
    date_start_day = date_start[6:8]
    _, num_days = calendar.monthrange(int(date_start_year), int(date_start_month))

    data = {}
    date_per_month = []
    for i in range(int(date_start_day), num_days + 1):
        if i < 10:
            i = f"0{i}"
        date_per_month.append(i)

    columns = [
        {
            "key": f"{i}.{date_start_month}.{date_start_year}",
            "field": f"{i}.{date_start_month}.{date_start_year}",
            "title": f"{i}.{date_start_month}.{date_start_year}",
            "align": 'center', "width": '30'}
        for i in date_per_month
    ]

    columns.insert(0, {"key": 'office', "field": 'office', "title": 'Офисы', "align": 'left', "width": 200})
    table_data = []

    if mode == "department":
        query_result = get_cash_resister_by_depatment_period(date_start, date_end)
        data = {}
        for qr in query_result:
            if not data.get(qr.department_id):
                data[qr.department_id] = {"office": qr.depart_name, **{f"{i}.{date_start_month}.{date_start_year}": "" for i in date_per_month }}
            tmp_office = data.get(qr.department_id)
            tmp_office[qr.char_day] = f"Наличные: {qr.received_cash} \n Терминал: {qr.received_terminal} \n" \
                                      f"Возврат нал: {qr.return_cash} \n Возврат терм: {qr.return_terminal} \n" \
                                      f"Всего: {qr.received_cash + qr.received_terminal - qr.return_cash - qr.return_terminal}"
            data[qr.department_id] = tmp_office.copy()
        table_data = [v for v in data.values()]

    return Response({"columns": columns, "tableData": table_data})
