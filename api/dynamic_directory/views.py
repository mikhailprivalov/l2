import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator

from dynamic_directory.models import Directory, DirectoryRecord, DirectoryRecordValue, DirectoryRecordVersion
from dynamic_directory.views import get_child_directories
from utils.response import status_response


@login_required
def list_directories(request):
    request_data = json.loads(request.body)
    q = request_data.get('q', '')

    return JsonResponse({'rows': get_child_directories(None, title_filter=q)})


@login_required
def list_directories_treeselect(request):
    return JsonResponse({'rows': [x.to_treeselect_json() for x in Directory.objects.filter(hide=False).order_by('title')]})


@login_required
def get_directory(request):
    request_data = json.loads(request.body)
    pk = request_data['pk']

    return JsonResponse(Directory.objects.get(pk=pk).to_json())


@login_required
def get_directory_rows(request):
    request_data = json.loads(request.body)
    pk = request_data['pk']
    page = request_data['page']
    q = (request_data.get('q') or '').strip() or None
    limit = 30
    directory: Directory = Directory.objects.get(pk=pk)
    fields = directory.get_fields()
    rows = []

    records = DirectoryRecord.objects.filter(directory=directory)
    if q:
        records = records.filter(Q(last_str_value__istartswith=q) | Q(title__istartswith=q) | Q(code__istartswith=q))
    records = records.order_by('title')
    p = Paginator(records, limit)

    for record in p.page(page).object_list:
        rows.append(record.get_last_version())

    return JsonResponse(
        {
            'fields': fields,
            'page': page,
            "pages": p.num_pages,
            'limit': limit,
            'rows': rows,
        }
    )


@login_required
def get_directory_one_row(request):
    request_data = json.loads(request.body)
    pk = request_data.get('pk')
    vpk = request_data.get('versionPk')

    if vpk:
        version: DirectoryRecordVersion = DirectoryRecordVersion.objects.get(pk=vpk)
        record: DirectoryRecord = version.record

        return JsonResponse(
            {
                'record': record.get_version(version.version),
            }
        )
    record: DirectoryRecord = DirectoryRecord.objects.get(pk=pk)

    return JsonResponse(
        {
            'record': record.get_last_version(),
        }
    )


@login_required
def get_suggests(request):
    pk = request.GET['pk']
    q = request.GET['value']
    directory: Directory = Directory.objects.get(pk=pk)
    records = DirectoryRecord.objects.filter(directory=directory).filter(Q(title__istartswith=q) | Q(last_str_value__istartswith=q)).order_by('title')[:15]

    return JsonResponse(
        {
            'data': [x.get_last_version() for x in records],
        }
    )


@login_required
def record_for_edit(request):
    request_data = json.loads(request.body)
    pk = request_data['pk']
    dpk = request_data['directory']
    directory: Directory = Directory.objects.get(pk=dpk)
    user_groups = [str(x) for x in request.user.groups.all()]
    if not any([str(x) in user_groups for x in directory.edit_access.all()]):
        return JsonResponse(None)

    fields = directory.get_fields_extended()
    record_params = {
        'title': '',
        'code': '',
        'lastVersion': -1,
        'hide': False,
    }

    if pk != -1:
        record: DirectoryRecord = DirectoryRecord.objects.get(pk=pk)
        record_params['title'] = record.title
        record_params['code'] = record.code
        record_params['lastVersion'] = record.last_version
        record_params['hide'] = record.hide
        last_version = DirectoryRecordVersion.objects.filter(record=record, version=record.last_version)[0]
        for f in fields:
            rv: DirectoryRecordValue = DirectoryRecordValue.objects.filter(record_version=last_version, field_id=f).first()
            if rv:
                if fields[f]['type'] == 4:
                    fields[f]['value'] = rv.linked_directory_record_id
                else:
                    fields[f]['value'] = rv.text_value

    return JsonResponse(
        {
            'directoryData': directory.to_json(),
            'recordParams': record_params,
            'fields': fields,
        }
    )


@login_required
def save_record(request):
    request_data = json.loads(request.body)
    pk = request_data['pk']
    dpk = request_data['directory']
    directory: Directory = Directory.objects.get(pk=dpk)
    user_groups = [str(x) for x in request.user.groups.all()]
    if not any([str(x) in user_groups for x in directory.edit_access.all()]):
        return status_response(False)

    fields = directory.get_fields_extended()
    request_fields = request_data['fields']
    record_params = request_data['recordParams']

    with transaction.atomic():
        if pk != -1:
            record: DirectoryRecord = DirectoryRecord.objects.get(pk=pk)
            if record.directory != directory:
                return status_response(False, 'Directory inconsistent')
            record.title = record_params['title']
            record.code = record_params['code']
            record.hide = record_params['hide']
            record.save()
        else:
            record: DirectoryRecord = DirectoryRecord.objects.create(
                directory=directory,
                title=record_params['title'],
                code=record_params['code'],
                hide=record_params['hide'],
                last_version=0,
            )

        v = record.last_version + 1
        directory.recuresive_updated_at_change()
        record.last_version = v
        record.save(update_fields=['last_version'])

        record_version: DirectoryRecordVersion = DirectoryRecordVersion.objects.filter(record=record, version=v - 1).first()
        if not record_version:
            record_version = DirectoryRecordVersion.objects.create(record=record, version=v)
        else:
            record_version.version = v
            record_version.save()

        for f in fields:
            rv: DirectoryRecordValue = DirectoryRecordValue.objects.filter(record_version=record_version, field_id=f).first()
            if not rv:
                rv = DirectoryRecordValue.objects.create(
                    record_version=record_version,
                    field_id=f,
                )

            val = request_fields.get(str(f), {}).get('value', '')

            if fields[f]['type'] == 4:
                rv.linked_directory_record_id = int(val) if isinstance(val, int) or val.isdigit() else None
                rv.text_value = ''
            else:
                rv.text_value = val
                rv.linked_directory_record_id = None
            rv.save()

        record.last_str_value = ''
        record.save()
        record.get_last_version()

    return status_response(True, data={'version': v})
