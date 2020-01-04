from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card
from directions.models import Issledovaniya, Napravleniya
from directory.models import Researches
from podrazdeleniya.models import Podrazdeleniya
from laboratory.decorators import group_required
import simplejson as json
from utils import tree_directions
from collections import OrderedDict
from copy import deepcopy


@login_required
@group_required("Врач стационара")
def load(request):
    data = json.loads(request.body)
    result = {"ok": False, "message": "Нет данных", "data": {}}
    pk = int(data["pk"])
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    for i in Issledovaniya.objects.filter(napravleniye__pk=pk, research__is_hospital=True):
        direction: Napravleniya = i.napravleniye
        card: Card = direction.client
        result["ok"] = True
        result["message"] = ""
        result["data"] = {
            "direction": direction.pk,
            "patient": {
                "fio_age": card.individual.fio(full=True),
                "card": card.number_with_type(),
                "base": card.base_id,
                "card_pk": card.pk,
                "individual_pk": card.individual_id,
            }
        }
        break
    return JsonResponse(result)


def hosp_get_data_direction(main_direction, site_type=-1, type_service='None', level=-1):
    # получить данные по разделу Стационарной карты
    # hosp_site_type=-1 - не получать ничего.
    # level уровень подчинения. Если вернуть только дочерние для текущего направления level=2
    result = tree_directions.get_research_by_dir(main_direction)
    num_iss = result[0][0]
    main_research = result[0][1]

    hosp_site_type = site_type
    hosp_level = level
    hosp_is_paraclinic, hosp_is_doc_refferal, hosp_is_lab, hosp_is_hosp = False, False, False, False
    if type_service == 'is_paraclinic':
        hosp_is_paraclinic = True
    elif type_service == 'is_doc_refferal':
        hosp_is_doc_refferal = True
    elif type_service == 'is_lab':
        hosp_is_lab = True

    hosp_dirs = tree_directions.hospital_get_direction(num_iss, main_research, hosp_site_type, hosp_is_paraclinic,
                                                       hosp_is_doc_refferal, hosp_is_lab, hosp_is_hosp, hosp_level)

    data = []
    if hosp_dirs:
        for i in hosp_dirs:
            data.append({'direction' : i[0], 'date_create' : i[1], 'time_create' : i[2], 'iss' : i[5], 'date_confirm' : i[6],
                         'time_confirm' : i[7], 'research_id' : i[8], 'research_title' : i[9], 'podrazdeleniye_id' : i[13],
                         'is_paraclinic' : i[14], 'is_doc_refferal' : i[15], 'is_stom' : i[16], 'is_hospital' : i[17],
                         'is_microbiology' : i[18], 'podrazdeleniye_title' : i[19], 'site_type' : i[21]})

    return data


def hosp_get_hosp_direction(num_dir):
    #возвращает дерево направлений-отделений, у к-рых тип улуги только is_hosp
    #[{'direction': номер направления, 'research_title': значение}, {'direction': номер направления, 'research_title': значение}]
    root_dir = tree_directions.root_direction(num_dir)
    num_root_dir = root_dir[-1][-3]
    result = tree_directions.get_research_by_dir(num_root_dir)
    num_iss = result[0][0]
    main_research = result[0][1]
    hosp_site_type = -1
    hosp_is_paraclinic, hosp_is_doc_refferal, hosp_is_lab = False, False, False
    hosp_is_hosp = True
    hosp_level = -1
    hosp_dirs = tree_directions.hospital_get_direction(num_iss, main_research, hosp_site_type, hosp_is_paraclinic,
                                                       hosp_is_doc_refferal, hosp_is_lab, hosp_is_hosp, hosp_level)


    data = [{'direction' : i[0], 'research_title' : i[9]} for i in hosp_dirs]

    return data


def hosp_get_curent_hosp_dir(current_iss):
    current_dir = Issledovaniya.objects.get(pk=current_iss).napravleniye
    hosp_dir = current_dir.parent.napravleniye_id
    return hosp_dir


def hosp_get_lab_iss(current_iss, extract=False):
    """
    агрегация результатов исследований
    возврат:  Если extract=True(выписка), то берем по всем hosp-dirs. Если эпикриз, то берем все исследования
    до текущего hosp-dirs
    Выход: {КДЛ:{vert:[{titile:'',fractions:[],results:[{date:"",values:[]}]}]},
        {horizont:[{titile:'', results:[{date:'',value:''},{date:'',value:''}]}]}}
    """

    num_dir = Issledovaniya.objects.get(pk=current_iss).napravleniye_id

    #получить все направления в истории по типу hosp
    hosp_dirs = hosp_get_hosp_direction(num_dir)

    #получить текущее направление типа hosp из текущего эпикриза
    current_dir = hosp_get_curent_hosp_dir(current_iss)

    if not extract:
        hosp_dirs = [i for i in hosp_dirs if i <= current_dir]

    #получить по каждому hosp_dirs Дочерние направления
    #TODO:

    #Получить титл подразделений типа Лаборатория
    departs_obj = Podrazdeleniya.objects.filter(p_type=2).order_by('title')
    departs = OrderedDict()
    result = OrderedDict()
    from .sql_func import get_research, get_iss, get_distinct_research, get_distinct_fraction, get_result_fraction
    for i in departs_obj:
        departs[i.pk] = i.title
        #получить research_id по лаборатории и vertical_result_display = True
        vertical = {}
        vertical_result = []
        result[i.title] = {'vertical' :{}}
        result[i.title] = {'horizontal' :{}}
        horizontal_result = []
        vertical_research = get_research(i.title, True)
        id_research_vertical = [i[0] for i in vertical_research]
        if len(id_research_vertical) > 0:
            #получить уникальные research_id по направления
            get_research_id = get_distinct_research(id_research_vertical, [106, 108,109, 107,112,113,114])
            research_distinct = [d[0] for d in get_research_id]
            if research_distinct:
                for id_research_vertical in research_distinct:
                    # получить исследования по направлениям и соответсвующим research_id
                    get_iss_id = get_iss(id_research_vertical, [106, 108,109, 107, 112,113,114])
                    iss_id_vertical = [i[0] for i in get_iss_id]

                    research_fraction_vertical = get_distinct_fraction(iss_id_vertical)
                    fraction_title = []
                    fraction_units = []
                    for f in research_fraction_vertical:
                        fraction_title.append(f[1])
                        fraction_units.append(f[2])
                    fraction_template = [''] * len(fraction_title)  # заготовка для value-резульлтатов
                    fraction_result = get_result_fraction(iss_id_vertical)
                    vertical_temp_results = {}
                    for f in fraction_result:
                        key = f'{f[4]} {str(f[5])}'
                        if key in vertical_temp_results.keys():
                            position_element = fraction_title.index(f[2])
                            tmp_list = vertical_temp_results.get(key)
                            tmp_list_vert = deepcopy(tmp_list)
                            tmp_list_vert[position_element] = f[3]
                            vertical_temp_results[key] = tmp_list_vert
                        else:
                            vertical_temp_results[key] = fraction_template
                            position_element = fraction_title.index(f[2])
                            tmp_list = vertical_temp_results.get(key)
                            tmp_list_vert = deepcopy(tmp_list)
                            tmp_list_vert[position_element] = f[3]
                            vertical_temp_results[key] = tmp_list_vert
                    vertical['title_research'] = Researches.objects.get(pk=id_research_vertical).title
                    vertical['title_fracions'] = fraction_title
                    vertical['result'] = vertical_temp_results
                    vertical1 = deepcopy(vertical)
                    vertical_result.append(vertical1)
                result[i.title]['vertical'] = vertical_result

        #получить research_id по лаборатории и vertical_result_display = False
        horizontal = {}
        horizontal_research = get_research(i.title, False)
        id_research_horizontal = [i[0] for i in horizontal_research]
        if len(id_research_horizontal) > 0:
            # получить исследования по направлениям и соответсвующим research_id для horizontal
            get_iss_id = get_iss(id_research_horizontal, [106, 108, 109, 107, 112,113,114])
            iss_id_horizontal = [i[0] for i in get_iss_id]
            #получить уникальные фракции по исследованиям для хоризонтал fraction_title: [], units: []
            if iss_id_horizontal:
                fraction_horizontal = get_distinct_fraction(iss_id_horizontal)
                fraction_title = []
                fraction_units = []
                for f in fraction_horizontal:
                    fraction_title.append(f[1])
                    fraction_units.append(f[2])

                fraction_template = [''] * len(fraction_title) # заготовка для value-резульлтатов
                fraction_result = get_result_fraction(iss_id_horizontal)

                temp_results = {}
                for f in fraction_result:
                    key = f'{f[4]} {str(f[5])}'
                    if key in temp_results.keys():
                        position_element = fraction_title.index(f[2])
                        tmp_list = temp_results.get(key)
                        tmp_list2 = deepcopy(tmp_list)
                        tmp_list2[position_element] = f[3]
                        temp_results[key] = tmp_list2
                    else:
                        temp_results[key] = fraction_template
                        position_element = fraction_title.index(f[2])
                        tmp_list = temp_results.get(key)
                        tmp_list2 = deepcopy(tmp_list)
                        tmp_list2[position_element] = f[3]
                        temp_results[key] = tmp_list2

                horizontal['title_fracions'] = fraction_title
                horizontal['result'] = temp_results
                horizontal_result.append(horizontal)
                result[i.title]['horizontal'] = horizontal_result

    return result
