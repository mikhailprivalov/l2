from astm import codec
import directions.models as directions
import directory.models as directory
import api.models as api


def GetIssDirection(dir: directions.Napravleniya, analyzer: api.Analyzer):
    r = []
    for i in directions.Issledovaniya.objects.filter(doc_confirmation__isnull=True):
        for fraction in directory.Fractions.objects.filter(research=i.research):
            pass
            #r.append(['O', 0, i.t])
    return r