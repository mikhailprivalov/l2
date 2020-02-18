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
    # print(data)
    # data1 = '{"directions":[113123, 113122], "exclude": {"titles": [], "dirDate": []}}'
    data = json.loads(data)
    print(data)
    print(data['directions'])
    exclude_direction = data['excluded']['dateDir']
    exclude_fraction = data['excluded']['titles']
    print(exclude_direction)
    print(exclude_fraction)
    a = hosp_get_lab_iss(None, False, [113122])
    print('from prepare', a)


def text_iss_to_pdf():
    pass
