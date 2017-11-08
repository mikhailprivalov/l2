from collections import defaultdict
import directions.models as directions
import directory.models as directory
import api.models as api


def get_iss_direction(direction: directions.Napravleniya, analyzer: api.Analyzer):
    r = []
    n = 0
    for i in directions.Issledovaniya.objects.filter(doc_confirmation__isnull=True, napravleniye=direction):
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
            researches[tube.pk].append(rel.astm_field)
        for tpk in researches:
            n += 1
            r.append(['O', n, tpk, [[None, x, None, None] for x in researches[tpk]], researches])
    return r
