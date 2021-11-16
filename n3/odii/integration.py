import logging
from typing import Union
import uuid
from urllib.parse import urljoin, urlencode
from django.utils import timezone

import requests

from laboratory.settings import N3_ODII_BASE_URL, N3_ODII_SYSTEM_ID, N3_ODII_TOKEN, RMIS_PROXY, DEFAULT_N3_DOCTOR

logger = logging.getLogger(__name__)


def get_url(path, query=None):
    if query is None:
        query = {}
    return urljoin(N3_ODII_BASE_URL, path) + ('?{}'.format(urlencode(query)) if query else '')


def make_request(path, query=None, as_json=True, **kwargs):
    if query is None:
        query = {}
    try:
        url = get_url(path, query=query)
        headers = {"Content-Type": "application/json", "Authorization": f"N3 {N3_ODII_TOKEN}"}
        data = requests.post(url, headers=headers, **kwargs, proxies=RMIS_PROXY)
        if as_json:
            return data.json()
        return data.text
    except Exception as e:
        print(e)  # noqa: T001
        return {}


def add_task_request(hospital_n3_id: str, patient_data: dict, direction_pk: int, fin_source_n3: str, service_n3_id: str, diagnosis: str, doc_data: dict) -> dict:
    ids = []
    is_all_correct_doc_data = bool(doc_data["snils"] and doc_data["position"] and doc_data["speciality"])

    if patient_data.get('enp'):
        ids.append(
            {
                "system": "urn:oid:1.2.643.2.69.1.1.1.6.228",
                "value": patient_data['enp'],
                "assigner": {
                    "display": "1.2.643.5.1.13.2.1.1.635.22001",
                },
            }
        )

    if patient_data.get("card", {}).get('numberWithType'):
        ids.append(
            {
                "system": "urn:oid:1.2.643.5.1.13.2.7.100.5",
                "value": patient_data["card"]['numberWithType'],
                "assigner": {
                    "display": N3_ODII_SYSTEM_ID,
                },
            }
        )

    if patient_data.get("passport_num") and patient_data.get("passport_serial"):
        patient_passport_issued = patient_data.get('passport_issued_orig', None)
        if "_" in patient_passport_issued or not patient_passport_issued:
            patient_passport_issued = "УФМС"
        ids.append(
            {
                "system": "urn:oid:1.2.643.2.69.1.1.1.6.14",
                "value": f"{patient_data['passport_serial']}:{patient_data['passport_num']}",
                "assigner": {
                    "display": patient_passport_issued,
                },
            }
        )

    if patient_data.get("snils"):
        ids.append(
            {
                "system": "urn:oid:1.2.643.2.69.1.1.1.6.223",
                "value": patient_data['snils'],
                "assigner": {
                    "display": 'ПФР',
                },
            }
        )

    doc_ids = []

    if doc_data.get('pk'):
        doc_ids.append(
            {
                "system": "urn:oid:1.2.643.5.1.13.2.7.100.5",
                "value": doc_data["pk"] if is_all_correct_doc_data else DEFAULT_N3_DOCTOR["pk"],
                "assigner": {
                    "display": N3_ODII_SYSTEM_ID,
                },
            }
        )

    if doc_data.get('snils'):
        doc_ids.append(
            {
                "system": "urn:oid:1.2.643.2.69.1.1.1.6.223",
                "value": doc_data['snils'] if is_all_correct_doc_data else DEFAULT_N3_DOCTOR["snils"],
                "assigner": {
                    "display": 'ПФР',
                },
            }
        )

    if not ids:
        return {
            'error': 'No patient ids',
        }

    if not doc_ids:
        return {
            'error': 'No doc ids',
        }

    patient_urn = f"urn:uuid:{str(uuid.uuid4())}"

    patient_resource = {
        "fullUrl": patient_urn,
        "resource": {
            "resourceType": "Patient",
            "identifier": ids,
            "name": [
                {
                    "family": patient_data['family'],
                    "given": [patient_data['name'], patient_data['patronymic']],
                },
            ],
            "gender": "male" if patient_data['sex'].lower() == "м" else "female",
            "birthDate": patient_data['birthday'],
            "managingOrganization": {
                "reference": f"Organization/{hospital_n3_id}",
            },
        },
    }

    condition_urn = f"urn:uuid:{str(uuid.uuid4())}"

    condition_resource = {
        "fullUrl": condition_urn,
        "resource": {
            "resourceType": "Condition",
            "verificationStatus": {"coding": [{"system": "urn:oid:2.16.840.1.113883.4.642.1.1075", "version": "1", "code": "provisional"}]},
            "category": [{"coding": [{"system": "urn:oid:1.2.643.2.69.1.1.1.36", "version": "1", "code": "diagnosis"}]}],
            "code": {"coding": [{"system": "urn:oid:1.2.643.2.69.1.1.1.2", "version": "1", "code": diagnosis.split()[0] if diagnosis and '.' in diagnosis else "Z00.0"}]},
            "subject": {"reference": patient_urn},
        },
    }

    encounter_urn = f"urn:uuid:{str(uuid.uuid4())}"

    encounter_resource = {
        "fullUrl": encounter_urn,
        "resource": {
            "resourceType": "Encounter",
            "identifier": [
                {
                    "system": f"urn:oid:{N3_ODII_SYSTEM_ID}",
                    "value": patient_data.get("card", {}).get('numberWithType'),
                    "assigner": {"display": patient_data.get("card", {}).get('numberWithType')},
                }
            ],
            "status": "in-progress",
            "class": {"system": "urn:oid:2.16.840.1.113883.1.11.13955", "version": "1", "code": "AMB"},
            "type": [{"coding": [{"system": "urn:oid:1.2.643.2.69.1.1.1.35", "version": "1", "code": "2"}]}],
            "subject": {"reference": patient_urn},
            "diagnosis": [{"condition": {"reference": condition_urn}}],
            "serviceProvider": {
                "reference": f"Organization/{hospital_n3_id}",
            },
        },
    }

    practitioner_urn = f"urn:uuid:{str(uuid.uuid4())}"

    practitioner_resource = {
        "fullUrl": practitioner_urn,
        "resource": {
            "resourceType": "Practitioner",
            "active": True,
            "identifier": doc_ids,
            "name": [
                {
                    "family": doc_data['family'] if is_all_correct_doc_data else DEFAULT_N3_DOCTOR["family"],
                    "given": [doc_data['name'], doc_data['patronymic']] if is_all_correct_doc_data else [DEFAULT_N3_DOCTOR['name'], DEFAULT_N3_DOCTOR['patronymic']],
                },
            ],
        },
        "request": {"method": "POST"},
    }

    requester_urn = f"urn:uuid:{str(uuid.uuid4())}"

    requester_resource = {
        "fullUrl": requester_urn,
        "resource": {
            "resourceType": "PractitionerRole",
            "active": True,
            "practitioner": {
                "reference": practitioner_urn,
            },
            "organization": {
                "reference": f"Organization/{hospital_n3_id}",
            },
            "code": [{"coding": [{"system": "urn:oid:1.2.643.5.1.13.13.11.1002", "version": "1", "code": doc_data.get('position') or '73'}]}],
            "specialty": [{"coding": [{"system": "urn:oid:1.2.643.5.1.13.13.11.1066", "version": "1", "code": doc_data.get('specialty') or "27"}]}],
        },
        "request": {"method": "POST"},
    }

    service_request_urn = f"urn:uuid:{str(uuid.uuid4())}"

    service_request_resource = {
        "fullUrl": service_request_urn,
        "resource": {
            "resourceType": "ServiceRequest",
            "intent": "filler-order",
            "code": {"coding": [{"system": "urn:oid:1.2.643.5.1.13.13.11.1471", "version": "6", "code": service_n3_id}]},
            "orderDetail": [{"coding": [{"system": "urn:oid:1.2.643.2.69.1.1.1.32", "version": "1", "code": fin_source_n3}]}],
            "subject": {"reference": patient_urn},
            "encounter": {"reference": encounter_urn},
            "requester": {"reference": requester_urn},
            "bodySite": [{"coding": [{"system": "urn:oid:1.2.643.2.69.1.1.1.58", "version": "1", "code": "2"}]}],
        },
    }

    task_urn = f"urn:uuid:{str(uuid.uuid4())}"

    task_resource = {
        "fullUrl": task_urn,
        "resource": {
            "resourceType": "Task",
            "identifier": [
                {
                    "system": f"urn:oid:{N3_ODII_SYSTEM_ID}",
                    "value": str(direction_pk),
                }
            ],
            "intent": "original-order",
            "authoredOn": timezone.now().isoformat(),
            "focus": {"reference": service_request_urn},
            "for": {"reference": patient_urn},
            "requester": {
                "reference": f"Organization/{hospital_n3_id}",
            },
            "owner": {
                "reference": f"Organization/{hospital_n3_id}",
            },
        },
    }

    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            patient_resource,
            condition_resource,
            encounter_resource,
            practitioner_resource,
            requester_resource,
            service_request_resource,
            task_resource,
        ],
    }

    return make_request('?_format=json', json=bundle)


def add_task_result(
    hospital_n3_id: str,
    patient_uuid: str,
    original_task_uuid: str,
    service_request_uuid: str,
    study_instance_uuid: Union[str, None],
    acsn_id: Union[str, None],
    direction_pk: int,
    service_n3_id: str,
    service_odii_type: int,
    executor_data: Union[dict, None],
    time_confirmation: str,
    pdf_content: Union[str, None],
) -> dict:
    entry = []

    if executor_data:
        executor_ids = []

        if executor_data.get('pk'):
            executor_ids.append(
                {
                    "system": "urn:oid:1.2.643.5.1.13.2.7.100.5",
                    "value": executor_data["pk"],
                    "assigner": {
                        "display": N3_ODII_SYSTEM_ID,
                    },
                }
            )

        if executor_data.get('snils'):
            executor_ids.append(
                {
                    "system": "urn:oid:1.2.643.2.69.1.1.1.6.223",
                    "value": executor_data['snils'],
                    "assigner": {
                        "display": 'ПФР',
                    },
                }
            )

        if not executor_ids:
            return {
                'error': 'No executor ids',
            }

        practitioner_urn = f"urn:uuid:{str(uuid.uuid4())}"

        practitioner_resource = {
            "fullUrl": practitioner_urn,
            "resource": {
                "resourceType": "Practitioner",
                "active": True,
                "identifier": executor_ids,
                "name": [
                    {
                        "family": executor_data['family'],
                        "given": [executor_data['name'], executor_data['patronymic']],
                    },
                ],
            },
            "request": {"method": "POST"},
        }

        entry.append(practitioner_resource)

        performer_urn = f"urn:uuid:{str(uuid.uuid4())}"

        performer_resource = {
            "fullUrl": performer_urn,
            "resource": {
                "resourceType": "PractitionerRole",
                "active": True,
                "practitioner": {
                    "reference": practitioner_urn,
                },
                "organization": {
                    "reference": f"Organization/{hospital_n3_id}",
                },
                "code": [{"coding": [{"system": "urn:oid:1.2.643.5.1.13.13.11.1002", "version": "1", "code": executor_data.get('position') or '73'}]}],
                "specialty": [{"coding": [{"system": "urn:oid:1.2.643.5.1.13.13.11.1066", "version": "1", "code": executor_data.get('specialty') or "27"}]}],
            },
            "request": {"method": "POST"},
        }

        entry.append(performer_resource)
    else:
        performer_urn = None

    if acsn_id and study_instance_uuid:
        image_study_urn = f"urn:uuid:{str(uuid.uuid4())}"

        image_study_resource = {
            "fullUrl": image_study_urn,
            "resource": {
                "resourceType": "ImagingStudy",
                "identifier": [
                    {"system": f"urn:oid:{N3_ODII_SYSTEM_ID}", "value": acsn_id, "type": {"coding": [{"system": "urn:oid:1.2.643.2.69.1.1.1.122", "version": "1", "code": "ACSN"}]}},
                    {"system": "urn:dicom:uid", "value": f"urn:oid:{study_instance_uuid}"},
                ],
                "status": "available",
                "subject": {"reference": f"Patient/{patient_uuid}"},
            },
        }
        entry.append(image_study_resource)
    else:
        image_study_urn = None

    if pdf_content:
        presented_form_urn = f"urn:uuid:{str(uuid.uuid4())}"

        presented_form_resource = {"fullUrl": presented_form_urn, "resource": {"resourceType": "Binary", "contentType": "application/pdf", "data": pdf_content}}
        entry.append(presented_form_resource)
    else:
        presented_form_urn = None

    diagnostic_report_urn = f"urn:uuid:{str(uuid.uuid4())}"

    diagnostic_report_resource = {
        "fullUrl": diagnostic_report_urn,
        "resource": {
            "resourceType": "DiagnosticReport",
            "meta": {"security": [{"code": "N"}]},
            "basedOn": {
                "reference": f"ServiceRequest/{service_request_uuid}",
            },
            "status": "final" if presented_form_urn else "partial",
            "category": {"coding": [{"system": "urn:oid:1.2.643.5.1.13.13.11.1472", "version": "1", "code": service_odii_type}]},
            "code": {"coding": [{"system": "urn:oid:1.2.643.5.1.13.13.11.1471", "version": "6", "code": service_n3_id}]},
            "subject": {"reference": f"Patient/{patient_uuid}"},
            "effectiveDateTime": time_confirmation,
            "issued": time_confirmation,
            "performer": [
                {
                    "reference": performer_urn,
                }
            ],
            **(
                {
                    "imagingStudy": [
                        {
                            "reference": image_study_urn,
                        }
                    ],
                }
                if image_study_urn
                else {}
            ),
            **(
                {
                    "presentedForm": [
                        {
                            "contentType": "application/pdf",
                            "url": presented_form_urn,
                        }
                    ]
                }
                if presented_form_urn
                else {}
            ),
        },
    }

    entry.append(diagnostic_report_resource)

    task_urn = f"urn:uuid:{str(uuid.uuid4())}"

    task_resource = {
        "fullUrl": task_urn,
        "resource": {
            "resourceType": "Task",
            "identifier": [
                {
                    "system": f"urn:oid:{N3_ODII_SYSTEM_ID}",
                    "value": f"{direction_pk}/{'completed' if presented_form_urn else 'in-progress'}",
                }
            ],
            "basedOn": {
                "reference": f"Task/{original_task_uuid}",
            },
            "status": "completed" if presented_form_urn else "in-progress",
            "intent": "reflex-order",
            "focus": {"reference": diagnostic_report_urn},
            "authoredOn": timezone.now().isoformat(),
            "for": {"reference": f"Patient/{patient_uuid}"},
            "requester": {
                "reference": f"Organization/{hospital_n3_id}",
            },
            "owner": {
                "reference": f"Organization/{hospital_n3_id}",
            },
        },
    }

    entry.append(task_resource)

    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": entry,
    }

    return make_request('?_format=json', json=bundle)
