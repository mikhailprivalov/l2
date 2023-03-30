from api.edit_forms.forms.implementations.employee_employee import EmployeeEmployeeForm
from api.edit_forms.forms.implementations.employee_position import EmployeePositionForm
from .employee_department import EmployeeDepartmentForm
from .employee_employee_position import EmployeeEmployeePositionForm


FORMS = {
    "employeeDepartment": EmployeeDepartmentForm,
    "employeeEmployeePosition": EmployeeEmployeePositionForm,
    "employeePosition": EmployeePositionForm,
    "employeeEmployee": EmployeeEmployeeForm,
}
