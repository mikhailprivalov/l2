import json
import logging

from django.contrib.auth.decorators import login_required

from api.edit_forms.forms.base import BaseForm, FormForbiddenException, FormNotFoundException, FormObjectNotFoundException, ObjectView
from api.edit_forms.forms.implementations import FORMS
from utils.response import status_response


logger = logging.getLogger(__name__)


@login_required
def form_markup(request):
    request_data = json.loads(request.body)
    form_type = request_data.get('formType')
    form_data = request_data.get('formData')

    try:
        if form_type not in FORMS:
            raise FormNotFoundException(f'Form {form_type} not found')

        form: BaseForm = FORMS[form_type]

        return status_response(True, data={"form": form.get_markup(request.user.doctorprofile, form_data)})
    except FormNotFoundException as e:
        logger.exception(e)
        return status_response(False, "Форма не найдена")
    except FormForbiddenException as e:
        logger.exception(e)
        return status_response(False, "Нет доступа к форме")
    except FormObjectNotFoundException as e:
        logger.exception(e)
        return status_response(False, str(e))
    except Exception as e:
        logger.exception(e)
        return status_response(False, "Неизвестная ошибка")


@login_required
def form_save(request):
    request_data = json.loads(request.body)
    form_type = request_data.get('formType')
    form_data = request_data.get('formData')

    try:
        if form_type not in FORMS:
            raise FormNotFoundException(f'Form {form_type} not found')

        form: BaseForm = FORMS[form_type]

        save_result = form.save(request.user.doctorprofile, form_data)

        return status_response(save_result['ok'], message=save_result.get('message'), data={"result": save_result['result']})
    except FormNotFoundException as e:
        logger.exception(e)
        return status_response(False, "Форма не найдена")
    except FormForbiddenException as e:
        logger.exception(e)
        return status_response(False, "Нет доступа к форме")
    except FormObjectNotFoundException as e:
        logger.exception(e)
        return status_response(False, str(e))
    except Exception as e:
        logger.exception(e)
        return status_response(False, "Неизвестная ошибка")


@login_required
def object_by_id(request):
    request_data = json.loads(request.body)
    form_type = request_data.get('formType')
    object_id = request_data.get('id')

    try:
        if form_type not in FORMS:
            raise FormNotFoundException(f'Form {form_type} not found')

        form: ObjectView = FORMS[form_type]

        if not issubclass(form, ObjectView):
            raise FormNotFoundException(f'Form {form_type} is not ObjectView')

        object = form.json_by_id(request.user.doctorprofile, object_id)

        if object is not None:
            return status_response(True, data={"object": object})
        else:
            return status_response(False, "Объект не найден")
    except FormNotFoundException as e:
        logger.exception(e)
        return status_response(False, "Форма не найдена")
    except FormForbiddenException as e:
        logger.exception(e)
        return status_response(False, "Нет доступа к форме")
    except FormObjectNotFoundException as e:
        logger.exception(e)
        return status_response(False, str(e))
    except Exception as e:
        logger.exception(e)
        return status_response(False, "Неизвестная ошибка")


@login_required
def objects_search(request):
    request_data = json.loads(request.body)
    form_type = request_data.get('formType')
    filters = request_data.get('filters')
    search = request_data.get('search')
    return_total_rows = request_data.get('returnTotalRows', False)
    as_treeselect = request_data.get('asTreeselect', False)
    page = request_data.get('page', 1)
    per_page = request_data.get('perPage', 30)
    sort_column = request_data.get('sortColumn')
    sort_direction = request_data.get('sortDirection')

    try:
        if form_type not in FORMS:
            raise FormNotFoundException(f'Form {form_type} not found')

        form: ObjectView = FORMS[form_type]

        if not issubclass(form, ObjectView):
            raise FormNotFoundException(f'Form {form_type} is not ObjectView')

        result = form.search(request.user.doctorprofile, page, per_page, sort_column, sort_direction, filters, return_total_rows, as_treeselect, search)

        if result is not None:
            return status_response(True, data={"result": result, "viewParams": form.view_params()})
        else:
            return status_response(False, "Объект не найден")
    except FormNotFoundException as e:
        logger.exception(e)
        return status_response(False, "Форма не найдена")
    except FormForbiddenException as e:
        logger.exception(e)
        return status_response(False, "Нет доступа к форме")
    except FormObjectNotFoundException as e:
        logger.exception(e)
        return status_response(False, str(e))
    except Exception as e:
        logger.exception(e)
        return status_response(False, "Неизвестная ошибка")
