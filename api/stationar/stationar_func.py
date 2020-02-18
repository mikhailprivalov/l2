from collections import OrderedDict
from copy import deepcopy

from directions.models import Issledovaniya, Napravleniya
from directory.models import Researches, HospitalService
from podrazdeleniya.models import Podrazdeleniya
from utils import tree_directions
from .sql_func import get_research, get_iss, get_distinct_research, get_distinct_fraction, get_result_fraction, \
    get_result_text_research


def hosp_get_data_direction(main_direction, site_type=-1, type_service='None', level=-1):
    # получить данные по разделу Стационарной карты
    # hosp_site_type=-1 - не получать ничего.
    # level уровень подчинения. Если вернуть только дочерние для текущего направления level=2
    result = tree_directions.get_research_by_dir(main_direction)
    num_iss = result[0][0]
    main_research = result[0][1]

    hosp_site_type = site_type
    hosp_level = level
    hosp_is_paraclinic, hosp_is_doc_refferal, hosp_is_lab, hosp_is_hosp, hosp_is_all = False, False, False, False, False
    if type_service == 'is_paraclinic':
        hosp_is_paraclinic = True
    elif type_service == 'is_doc_refferal':
        hosp_is_doc_refferal = True
    elif type_service == 'is_lab':
        hosp_is_lab = True
    if site_type == -1 and type_service == 'None':
        hosp_is_all = True

    hosp_dirs = tree_directions.hospital_get_direction(num_iss, main_research, hosp_site_type, hosp_is_paraclinic,
                                                       hosp_is_doc_refferal, hosp_is_lab, hosp_is_hosp, hosp_level,
                                                       hosp_is_all)

    data = []
    if hosp_dirs:
        for i in hosp_dirs:
            data.append({'direction': i[0], 'date_create': i[1], 'time_create': i[2], 'iss': i[5], 'date_confirm': i[6],
                         'time_confirm': i[7], 'research_id': i[8], 'research_title': i[9], 'podrazdeleniye_id': i[13],
                         'is_paraclinic': i[14], 'is_doc_refferal': i[15], 'is_stom': i[16], 'is_hospital': i[17],
                         'is_microbiology': i[18], 'podrazdeleniye_title': i[19], 'site_type': i[21],
                         'research_short_title': i[23], 'is_slave_hospital': i[24]})

    return data


def get_direction_attrs(direction, site_type=-1, type_service='None', level=-1):
    # Возврат: [{pk:№, date_create:'', confirm:'', researches:[]}, {pk:№, date_create:'', confirm:'', researches:[]}]
    data = []

    main_direction = direction
    type_serv = type_service
    site_type_num = site_type
    level_get = level
    data_direction = hosp_get_data_direction(main_direction, site_type=site_type_num, type_service=type_serv,
                                             level=level_get)
    dict_temp = {}

    for dir_attr in data_direction:
        num_dir = dir_attr.get('direction')
        if dict_temp.get(num_dir):
            dict_by_dir = dict_temp.get(num_dir)
            dict_by_dir['researches'] = [*dict_by_dir['researches'], dir_attr.get('research_title')]
            dict_by_dir['researches_short'] = [*dict_by_dir['researches_short'], dir_attr.get('researches_short')]
            dict_temp[num_dir] = dict_by_dir.copy()
        else:
            type_dir = 'directions'
            confirm = bool(dir_attr.get('date_confirm'))
            if dir_attr.get('is_slave_hospital'):
                type_dir = 'stationar'
            dict_temp[num_dir] = {'type': type_dir,
                                  'date_create': dir_attr.get('date_create'),
                                  'confirm': confirm,
                                  'researches': [dir_attr.get('research_title')],
                                  'researches_short': [dir_attr.get('research_short_title')],
                                  'podrazdeleniye': dir_attr.get('podrazdeleniye_title'), }

    for k, v in dict_temp.items():
        dict_result = {'type': v['type'], 'pk': k, 'date_create': v['date_create'], 'confirm': v['confirm'],
                       'researches': v['researches'],
                       'researches_short': v['researches_short'], 'podrazdeleniye': v['podrazdeleniye']}
        data.append(dict_result)

    return data


def hosp_get_hosp_direction(num_dir):
    # возвращает дерево направлений-отделений, у к-рых тип улуги только is_hosp
    # [{'direction': номер направления, 'research_title': значение}, {'direction': номер направления, 'research_title': значение}]
    root_dir = tree_directions.root_direction(num_dir)
    num_root_dir = root_dir[-1][-3]
    result = tree_directions.get_research_by_dir(num_root_dir)
    num_iss = result[0][0]
    main_research = result[0][1]
    hosp_site_type = -1
    hosp_is_paraclinic, hosp_is_doc_refferal, hosp_is_lab, hosp_is_all = False, False, False, False
    hosp_is_hosp = True
    hosp_level = -1
    hosp_dirs = tree_directions.hospital_get_direction(num_iss, main_research, hosp_site_type, hosp_is_paraclinic,
                                                       hosp_is_doc_refferal, hosp_is_lab, hosp_is_hosp, hosp_level,
                                                       hosp_is_all)

    data = [{'direction': i[0], 'research_title': i[9]} for i in hosp_dirs if not i[25]]

    return data


def hosp_get_curent_hosp_dir(current_iss):
    obj_iss = Issledovaniya.objects.get(pk=current_iss)
    current_dir = obj_iss.napravleniye
    if obj_iss.research.is_hospital:
        return current_dir.pk
    if current_dir.parent:
        return current_dir.parent.napravleniye_id


def hosp_get_lab_iss(current_iss, extract=False, *directions):
    """
    агрегация результатов исследований
    возврат:  Если extract=True(выписка), то берем по всем hosp-dirs. Если эпикриз, то берем все исследования
    до текущего hosp-dirs
    Выход: {КДЛ:{vert:[{titile:'',fractions:[],results:[{date:"",values:[]}]}]},
        {horizont:[{titile:'', results:[{date:'',value:''},{date:'',value:''}]}]}}
    """
    if not directions:
        obj_iss = Issledovaniya.objects.get(pk=current_iss)
        num_dir = obj_iss.napravleniye_id

        # получить все направления в истории по типу hosp
        hosp_dirs = hosp_get_hosp_direction(num_dir)

        # получить текущее направление типа hosp из текущего исследования
        current_dir = hosp_get_curent_hosp_dir(current_iss)
        # проверить - это переводной эпикриз
        epicris = False
        if obj_iss.research.is_slave_hospital:
            obj_hospital_service = HospitalService.objects.filter(slave_research=obj_iss.research).first().site_type
            if obj_hospital_service == 6:
                epicris = True

        if epicris:
            hosp_dirs = [i for i in hosp_dirs if i["direction"] <= current_dir]

        num_lab_dirs = set()
        if (not extract) and (not epicris):
            obj_hosp_dirs = hosp_get_data_direction(current_dir, site_type=-1, type_service='is_lab', level=2)
            for k in obj_hosp_dirs:
                lab_dir = k.get('direction')
                num_lab_dirs.add(lab_dir)

        # получить по каждому hosp_dirs Дочерние направления по типу лаборатория
        if extract or epicris:
            for h in hosp_dirs:
                obj_hosp_dirs = hosp_get_data_direction(h["direction"], site_type=-1, type_service='is_lab', level=2)
                for k in obj_hosp_dirs:
                    lab_dir = k.get('direction')
                    num_lab_dirs.add(lab_dir)
    if directions:
        num_lab_dirs = directions

    num_lab_dirs = list(num_lab_dirs)
    if len(num_lab_dirs) == 0:
        return {}

    # Получить титл подразделений типа Лаборатория
    departs_obj = Podrazdeleniya.objects.filter(p_type=2).order_by('title')
    departs = OrderedDict()
    result = OrderedDict()

    for i in departs_obj:
        departs[i.pk] = i.title
        # получить research_id по лаборатории и vertical_result_display = True
        vertical = {}
        vertical_result = []
        result[i.title] = {'vertical': {}, 'horizontal': {}}
        horizontal_result = []
        vertical_research = get_research(i.title, True)
        id_research_vertical = [i[0] for i in vertical_research]
        if len(id_research_vertical) > 0:
            # получить уникальные research_id по направления
            get_research_id = get_distinct_research(id_research_vertical, num_lab_dirs, is_text_research=False)
            research_distinct = [d[0] for d in get_research_id]
            if research_distinct:
                for id_research_vertical in research_distinct:
                    # получить исследования по направлениям и соответсвующим research_id
                    get_iss_id = get_iss(id_research_vertical, num_lab_dirs)
                    iss_id_vertical = [i[0] for i in get_iss_id]

                    research_fraction_vertical = get_distinct_fraction(iss_id_vertical)
                    fraction_title = []
                    fraction_title_units = []
                    for f in research_fraction_vertical:
                        fraction_title.append(f[1])
                        title_unit = f', {f[2]}' if f[2] else ''
                        fraction_title_units.append(f'{f[1]}{title_unit}')
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
                    vertical['title_fracions'] = fraction_title_units
                    vertical['result'] = vertical_temp_results
                    vertical1 = deepcopy(vertical)
                    vertical_result.append(vertical1)
                result[i.title]['vertical'] = vertical_result

        # получить research_id по лаборатории и vertical_result_display = False
        horizontal = {}
        horizontal_research = get_research(i.title, False)
        id_research_horizontal = [i[0] for i in horizontal_research]
        if len(id_research_horizontal) > 0:
            # получить исследования по направлениям и соответсвующим research_id для horizontal
            get_iss_id = get_iss(id_research_horizontal, num_lab_dirs)
            iss_id_horizontal = [i[0] for i in get_iss_id]
            # получить уникальные фракции по исследованиям для хоризонтал fraction_title: [], units: []
            if iss_id_horizontal:
                fraction_horizontal = get_distinct_fraction(iss_id_horizontal)
                fraction_title = []
                fraction_title_units = []
                for f in fraction_horizontal:
                    fraction_title.append(f[1])
                    title_unit = f', {f[2]}' if f[2] else ''
                    fraction_title_units.append(f'{f[1]}{title_unit}')

                fraction_template = [''] * len(fraction_title)  # заготовка для value-резульлтатов
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

                horizontal['title_fracions'] = fraction_title_units
                horizontal['result'] = temp_results
                horizontal_result.append(horizontal)
                result[i.title]['horizontal'] = horizontal_result
    result_filtered = {}
    for k in result:
        if result[k]['horizontal'] or result[k]['vertical']:
            result_filtered[k] = result[k]
    return result_filtered


def hosp_get_text(current_iss, extract=False, mode=None):
    # # Возврат стр-ра:
    # {'paraclinic': [{'title_research': 'Проведение электрокардиографических исследований ( ЭКГ )', 'result': [
    #                 {'date': '05.01.20 117', 'data': [{'group_title': '', 'fields': [{'title_field': 'Заключение',
    #                       'value': 'Повышение пучка Гиса'}]}]},
    #                 {'date': '05.01.20 119', 'data': [{'group_title': '', 'fields': [{'title_field': 'Заключение',
    #                       'value': 'Диффузные нарушения'}]}]}]} ]}]
    #                                                                                                                     ]}
    if mode is None:
        return {}
    num_dir = Issledovaniya.objects.get(pk=current_iss).napravleniye_id
    # получить все направления в истории по типу hosp
    hosp_dirs = hosp_get_hosp_direction(num_dir)

    # получить текущее направление типа hosp из текущего эпикриза
    current_dir = hosp_get_curent_hosp_dir(current_iss)
    if not extract:
        hosp_dirs = [i for i in hosp_dirs if i["direction"] <= current_dir]

    # получить по каждому hosp_dirs Дочерние направления по типу is_paraclinic, is_doc_refferal
    num_paraclinic_dirs = set()
    for h in hosp_dirs:
        obj_hosp_dirs = hosp_get_data_direction(h["direction"], site_type=-1, type_service=mode, level=2)
        if not obj_hosp_dirs:
            continue
        for k in obj_hosp_dirs:
            paraclinic_dir = k.get('direction')
            num_paraclinic_dirs.add(paraclinic_dir)

    num_paraclinic_dirs = list(num_paraclinic_dirs)
    # [0] - заглушка для запроса. research c id =0 не бывает
    get_research_id = get_distinct_research([0], num_paraclinic_dirs, is_text_research=True) if num_paraclinic_dirs else []
    research_distinct = [d[0] for d in get_research_id]
    result = []

    for research in research_distinct:
        field_result = get_result_text_research(research, num_paraclinic_dirs)
        last_group = None
        last_date = None
        data_in = []
        new_date_data = {}
        for i in field_result:
            date = f'{i[1]} {i[2]}'
            group = i[3]
            fields = {'title_field': i[4], 'value': i[5]}

            if date != last_date:
                if new_date_data:
                    data_in.append(new_date_data.copy())

                new_date_data = {}
                new_date_data['date'] = date
                new_date_data['data'] = [{'group_title': group, 'fields': [fields.copy()]}]
                last_date = date
                last_group = group
                continue

            if group != last_group and date == last_date:
                current_data = new_date_data.get('data')
                current_data.append({'group_title': group, 'fields': [fields.copy()]})
                new_date_data['data'] = current_data.copy()
                last_group = group
                continue

            current_data = new_date_data.get('data')
            get_last_group = current_data.pop()
            last_fields = get_last_group.get('fields')
            last_fields.append(fields.copy())
            get_last_group['fields'] = last_fields.copy()
            current_data.append(get_last_group.copy())
            new_date_data['data'] = current_data.copy()

        data_in.append(new_date_data.copy())

        temp_result = {}
        temp_result['title_research'] = Researches.objects.get(pk=research).title
        temp_result['result'] = data_in.copy()
        result.append(temp_result.copy())

    return result


def hosp_get_text_iss(current_iss, is_extract, mode):
    if mode is None:
        return []
    if mode == 'desc':
        modes = [
            'is_paraclinic',
            'is_doc_refferal',
        ]
    else:
        modes = [mode]

    v = []

    for m in modes:
        v.extend(hosp_get_text(current_iss, is_extract, mode=m))

    return v


def forbidden_edit_dir(num_dir):
    """
    Проверяет подтверждена ли выписка, или переводной эпикриз. И возвращает True|False - для редактирвоания протколов
    """
    # (если услуга имеет тип is_doc_refferal, или is_paraclinic) и направление не имеет parent услугу типа hosp вернуть False
    obj_iss = Issledovaniya.objects.filter(napravleniye_id=num_dir).first()
    parent = Napravleniya.objects.get(pk=num_dir).parent
    if not parent and (obj_iss.research.is_doc_refferal or obj_iss.research.is_paraclinic):
        return False

    if parent:
        parent_is_hospital = parent.research.is_hospital
        if (obj_iss.research.is_doc_refferal or obj_iss.research.is_paraclinic) and not parent_is_hospital:
            return False

    hosp_nums_obj = hosp_get_hosp_direction(num_dir)
    hosp_last_num = hosp_nums_obj[-1].get('direction')
    hosp_extract = hosp_get_data_direction(hosp_last_num, site_type=7, type_service='None', level=2)
    if hosp_extract and hosp_extract[0].get('date_confirm'):
        return True

    if not hosp_extract or not hosp_extract[0].get('date_confirm'):
        # Проверить подтверждение переводного эпикриза
        # Получить hosp_dir для текужего направления
        current_iss = Issledovaniya.objects.get(napravleniye_id=num_dir)
        current_dir_hosp_dir = num_dir
        if not current_iss.research.is_hospital:
            current_dir_hosp_dir = hosp_get_curent_hosp_dir(current_iss.pk)
        # получить для текущего hosp_dir эпикриз с title - перевод.....
        epicrisis_data = hosp_get_data_direction(current_dir_hosp_dir, site_type=6, type_service='None', level=2)
        if epicrisis_data:
            result_check = check_transfer_epicrisis(epicrisis_data)
            return result_check['is_transfer']
    return False


def check_transfer_epicrisis(data):
    for i in data:
        if i.get("research_title").lower().find('перевод') != -1:
            if i.get('date_confirm'):
                return {'is_transfer': True, 'iss': i.get('iss'), 'research_id': i.get('research_id')}
    return {'is_transfer': False, 'iss': None, 'research_id': None}
