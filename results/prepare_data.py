from api.stationar.stationar_func import hosp_get_lab_iss
import json
# field_type
# (16, 'Agg lab'),
# (17, 'Agg desc')
# {
# directions: [],
# exclude: {
#     titles: [],
#     dirDate: [],
# }
# }

def lab_iss_to_pdf(data):
    data1 = '{"directions":[113123, 113122], "exclude": {"titles": [], "dirDate": []}}'
    directions = json.loads(data1)
    print(directions, type(directions))
    # a = hosp_get_lab_iss(None, False, directions)
    print('from prepare')


def text_iss_to_pdf():
    pass
