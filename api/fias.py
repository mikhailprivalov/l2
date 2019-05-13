import json
import requests
from appconf.manager import SettingManager

BASE_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/{}"


def suggest(query, resource='address', count=5):
    k = SettingManager.get("dadata_key", default='', default_type='s')
    if not k:
        return []
    url = BASE_URL.format(resource)
    headers = {"Authorization": "Token {}".format(k),
               "Content-Type": "application/json"}
    data = {"query": query, "count": count,
            "locations_boost": [{
                "kladr_id": SettingManager.get("dadata_kladr_prior_city", default='38', default_type='s')
            }]
        }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    return list(map(lambda x: x.get('value', ''), r.json().get('suggestions', [])))
