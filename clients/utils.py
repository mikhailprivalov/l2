from clients.models import Individual, Card


def find_patient(snils, enp):
    snils = ''.join(ch for ch in snils if ch.isdigit())

    individual = None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        individual = individuals.first()

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title='СНИЛС')
        individual = individuals.first()

    if not individual:
        return None

    card = Card.objects.filter(individual=individual, base__internal_type=True, is_archive=False).first()
    return card
