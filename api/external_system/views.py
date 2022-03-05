import json
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from appconf.manager import SettingManager
from laboratory.settings import BASE_DIR


@login_required
def get_phones_transfers(request):
    phones_transfer = SettingManager.get("phones_transfer_file", default='False', default_type='b')
    org_phones = []
    extrenal_phones = []

    if phones_transfer:
        try:
            phones_transfer_file = os.path.join(BASE_DIR, 'external_system', 'settings', 'phones_org.json')
            with open(phones_transfer_file) as json_file:
                org_phones = json.load(json_file)
        except Exception:
            org_phones = []

    if phones_transfer:
        try:
            extrenal_phones_file = os.path.join(BASE_DIR, 'external_system', 'settings', 'extrenal_phones.json')
            with open(extrenal_phones_file) as json_file:
                extrenal_phones = json.load(json_file)
        except Exception:
            extrenal_phones = []

    return JsonResponse({"org_phones": list(org_phones), "extrenal_phones": list(extrenal_phones)})
