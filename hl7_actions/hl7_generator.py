from datetime import datetime
from jinja2 import FileSystemLoader, Environment


def create_sample_data(data_patient, obr_data, pdf_base64):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")

    return {
        "message_datetime": current_time,
        "message_control_id": "123456",
        "pid_segment": {
            "patient_id": data_patient.get("patient_id"),
            "patient_name": f"{data_patient.get('patient_fio')}^{data_patient.get('patient_name')}^{data_patient.get('patient_patronymic')}",
            "datetime_of_birth": data_patient.get('patine_birthday'),
            "sex": data_patient.get('sex'),
        },
        "obr": obr_data,
        "pdf_base64": pdf_base64
    }


class HL7Generator:
    def __init__(self, template_dir):
        self.env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)
        self.template = self.env.get_template("hl7_result_base.jinja2")

    def generate_hl7_message(self, data):
        return self.template.render(**data)
