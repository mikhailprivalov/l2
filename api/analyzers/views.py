import subprocess

from api.models import Analyzer, Application
from api.models import ManageDoctorProfileAnalyzer

import simplejson as json
from django.http import JsonResponse


def all_analyzers(request):
    analyzers = [{"label": analyzer.title, "pk": analyzer.id} for analyzer in Analyzer.objects.all().exclude(service_name=None).exclude(port=None).order_by('title', 'id')]
    return JsonResponse({"data": analyzers})


def analyzers_load_file(request):
    analyzers = [{"label": analyzer.name, "id": analyzer.id} for analyzer in Application.objects.filter(can_load_file_result=True).order_by('name', 'id')]
    return JsonResponse({"data": analyzers})


def restart_analyzer(request):
    request_data = json.loads(request.body)
    su = request.user.is_superuser
    if su:
        name_obj = Analyzer.objects.filter(id=request_data["pk"]).first()
        name = name_obj.service_name
    else:
        name_obj = ManageDoctorProfileAnalyzer.objects.filter(analyzer_id=request_data["pk"], doctor_profile_id=request.user.doctorprofile.pk).first()
        name = name_obj.analyzer.service_name
    restart_service = subprocess.Popen(["systemctl", "--user", "restart", name])
    restart_service.wait()
    result = get_status_analyzer(request_data["pk"])
    return JsonResponse({"data": result})


def manage_profile_analyzer(request):
    current_user = request.user.doctorprofile.pk
    su = request.user.is_superuser
    if su:
        filter_analyzer = [{"label": g.title, "pk": g.pk} for g in Analyzer.objects.all().exclude(service_name=None).exclude(port=None).order_by('title', 'pk')]
    else:
        filter_analyzer = [
            {"label": g.analyzer.title, "pk": g.analyzer_id}
            for g in ManageDoctorProfileAnalyzer.objects.filter(doctor_profile_id=current_user).exclude(analyzer__service_name=None).exclude(analyzer__port=None).order_by('analyzer', 'id')
        ]
    return JsonResponse({"data": filter_analyzer})


def status_analyzer(request):
    request_data = json.loads(request.body)
    result = get_status_analyzer(request_data["pk"])
    return JsonResponse({"data": result})


def status_systemctl(request):
    request_data = json.loads(request.body)
    result = get_status_systemctl(request_data["pk"])
    return JsonResponse({"data": result})


def get_status_analyzer(pk):
    port = Analyzer.objects.values_list('port', flat=True).get(id=pk)
    lsof_command = ['lsof', '-i', f':{port}']
    process = subprocess.Popen(lsof_command, stdout=subprocess.PIPE)
    output, error = process.communicate()
    res = output.decode().replace(' ', ',')
    res = res.split('\n')
    result = []
    step = 0
    for i in res:
        tmp_res = i.split(',')
        tmp_res = [x for x in tmp_res if x]
        if len(tmp_res) != 0:
            if step != 0:
                a = [tmp_res[1], tmp_res[-1], tmp_res[-2]]
                result.append(a)
            step += 1
    result = [{"pk": pk, "status": i} for i in result]
    return result


def get_status_systemctl(pk):
    service_name = Analyzer.objects.values_list('service_name', flat=True).get(id=pk)
    systemd_command = ['systemctl', '--user', 'status', f'{service_name}']
    proc = subprocess.Popen(systemd_command, stdout=subprocess.PIPE)
    output, error = proc.communicate()
    result = output.decode()
    result = result.split('\n')
    result = [{"pk": pk, "status": i} for i in result]
    return result
