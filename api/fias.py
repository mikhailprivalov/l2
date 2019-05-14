import pickle

import simplejson as json
from django.core.cache import cache
import requests
from appconf.manager import SettingManager
from rmis_integration.client import get_md5

BASE_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/{}"


def suggest(query, resource='address', count=5):
    k = SettingManager.get("dadata_key", default='', default_type='s')
    if not k:
        return []
    key = get_md5('{}{}{}'.format(k, resource, query))
    l = cache.get(key)
    if not l:
        url = BASE_URL.format(resource)
        headers = {"Authorization": "Token {}".format(k),
                   "Content-Type": "application/json"}
        data = {"query": query, "count": count,
                "locations_boost": [{
                    "kladr_id": SettingManager.get("dadata_kladr_prior_city", default='38', default_type='s')
                }]
            }
        r = requests.post(url, data=json.dumps(data), headers=headers)
        l = list(map(lambda x: x.get('value', ''), r.json().get('suggestions', [])))
        cache.set(key, pickle.dumps(l, protocol=4), 24 * 3600)
    else:
        l = pickle.loads(l, encoding="utf8")

    return l
