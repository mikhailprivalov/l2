import itertools
from collections import defaultdict

import simplejson as json
from astm import codec
from django.utils import timezone

import api.models as api
import directions.models as directions
import directory.models as directory


def get_astm_header() -> list:
    return ['H|\\^&', None, None, ['1', '2.00'], None, None, None, None, None, None, 'P', '1.00', timezone.now().strftime("%Y%m%d%H%M%S")]


def get_leave() -> list:
    return ['L', 1, 'N']


def get_patient() -> list:
    return ['P', 1]


def get_iss_direction(direction: directions.Napravleniya, analyzer: api.Analyzer, full=False) -> list:
    r = []
    n = 0
    iss_list = directions.Issledovaniya.objects.filter(napravleniye=direction)
    if not full:
        iss_list = iss_list.filter(time_confirmation__isnull=True)
    for i in iss_list:
        researches = defaultdict(list)
        for fraction in directory.Fractions.objects.filter(research=i.research, relationfractionastm__analyzer=analyzer, hide=False):
            rel = api.RelationFractionASTM.objects.filter(fraction=fraction, analyzer=analyzer)
            if not rel.exists():
                continue
            rel = rel[0]
            tube = directions.TubesRegistration.objects.filter(type__fractions=fraction)
            if not tube.exists():
                continue
            tube = tube[0]
            researches[tube.number].append(rel.astm_field)
        for tpk in researches:
            n += 1
            r.append(['O', n, tpk, None, [[None, x, None, None] for x in researches[tpk]]])
    return r


def encode(m) -> str:
    return codec.iter_encode(m)


def get_astm(directions_list, analyzer: api.Analyzer, full=False, out=None) -> str:
    iss = [get_iss_direction(x, analyzer, full) for x in directions_list]
    m = [get_astm_header(), get_patient()]
    m = list(itertools.chain(m, *iss))
    m.append(get_leave())
    if out:
        out.write(json.dumps(m))
    return encode(m)


def get_iss_astm(issledovaniya: list, app: api.Application, need_astm=False):
    m = [get_astm_header(), get_patient()]
    n = 0

    researches = defaultdict(list)
    for row in issledovaniya:
        k = row["pk"]
        i = row["iss"]
        for fraction in directory.Fractions.objects.filter(research=i.research, relationfractionastm__application_api=app, hide=False):
            rel = api.RelationFractionASTM.objects.filter(fraction=fraction, application_api=app)
            if not rel.exists():
                continue
            rel = rel[0]
            if rel.is_code:
                researches[k].append([None, None, None, rel.astm_field])
            else:
                researches[k].append([None, rel.astm_field, None, None])
    for tpk in researches:
        n += 1
        m.append(['O', n, tpk, None, researches[tpk]])
    m.append(get_leave())
    return encode(m)
