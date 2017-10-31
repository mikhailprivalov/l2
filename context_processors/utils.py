import clients.models as Clients
import simplejson as json


def card_bases(request):
    card_bases_vars = []
    for b in Clients.CardBase.objects.filter(hide=False).order_by("pk"):
        card_bases_vars.append(dict(title=b.title, code=b.short_title, pk=b.pk, history_number=b.history_number))
    return {"card_bases": json.dumps(card_bases_vars)}
