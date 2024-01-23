from collections import OrderedDict
from copy import deepcopy
from typing import List

from directions.models import Issledovaniya, Napravleniya
from directory.models import Researches, HospitalService
from podrazdeleniya.models import Podrazdeleniya
from utils import tree_directions
from .sql_func import (
    get_research,
    get_iss,
    get_distinct_research,
    get_distinct_fraction,
    get_result_fraction,
    get_result_text_research,
    get_result_temperature_list,
    get_assignments_by_history,
)
from api.dicom import search_dicom_study
from utils.dates import normalize_date
from anytree import Node, RenderTree


def hosp_get_data_direction(main_direction, site_type=-1, type_service='None', level=-1):
    # Получить данные по разделу Стационарной карты
    # hosp_site_type=-1 - не получать ничего.
    # level уровень подчинения. Если вернуть только дочерние для текущего направления level=2
    result = tree_directions.get_research_by_dir(main_direction)
    num_iss = result[0][0]
    main_research = result[0][1]

    hosp_site_type = site_type
    hosp_level = level
    hosp_is_paraclinic, hosp_is_doc_refferal, hosp_is_lab, hosp_is_hosp, hosp_is_all, hosp_morfology, hosp_form = False, False, False, False, False, False, False
    if type_service == 'is_paraclinic':
        hosp_is_paraclinic = True
    elif type_service == 'is_doc_refferal':
        hosp_is_doc_refferal = True
    elif type_service == 'is_lab':
        hosp_is_lab = True
    elif type_service == 'is_morfology':
        hosp_morfology = True
    elif type_service == 'is_form':
        hosp_form = True
    if site_type == -1 and type_service == 'None':
        hosp_is_all = True

    hosp_dirs = tree_directions.hospital_get_direction(
        num_iss, main_research, hosp_site_type, hosp_is_paraclinic, hosp_is_doc_refferal, hosp_is_lab, hosp_is_hosp, hosp_level, hosp_is_all, hosp_morfology, hosp_form
    )

    data = []
    if hosp_dirs:
        for i in hosp_dirs:
            if hosp_is_all and i[21] == 9:
                continue
            data.append(
                {
                    'direction': i[0],
                    'date_create': i[1],
                    'time_create': i[2],
                    'iss': i[5],
                    'date_confirm': i[6],
                    'time_confirm': i[7],
                    'research_id': i[8],
                    'research_title': i[9],
                    'podrazdeleniye_id': i[13],
                    'is_paraclinic': i[14],
                    'is_doc_refferal': i[15],
                    'is_stom': i[16],
                    'is_hospital': i[17],
                    'is_microbiology': i[18],
                    'podrazdeleniye_title': i[19],
                    'site_type': i[21],
                    'research_short_title': i[23],
                    'is_slave_hospital': i[24] or hosp_form,
                    'is_cancel': i[25],
                    "is_citology": i[26],
                    "is_gistology": i[27],
                    "is_form": i[28],
                }
            )

    return data


def get_direction_attrs(direction, site_type=-1, type_service='None', level=-1):
    # Возврат: [{pk:№, date_create:'', confirm:'', researches:[]}, {pk:№, date_create:'', confirm:'', researches:[]}]
    data = []

    main_direction = direction
    type_serv = type_service
    site_type_num = site_type
    level_get = level
    data_direction = hosp_get_data_direction(main_direction, site_type=site_type_num, type_service=type_serv, level=level_get)
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
            dict_temp[num_dir] = {
                'type': type_dir,
                'date_create': dir_attr.get('date_create'),
                'confirm': confirm,
                'researches': [dir_attr.get('research_title')],
                'researches_short': [dir_attr.get('research_short_title')],
                'podrazdeleniye': dir_attr.get('podrazdeleniye_title'),
            }

    for k, v in dict_temp.items():
        dict_result = {
            'type': v['type'],
            'pk': k,
            'date_create': v['date_create'],
            'confirm': v['confirm'],
            'researches': v['researches'],
            'researches_short': v['researches_short'],
            'podrazdeleniye': v['podrazdeleniye'],
        }
        data.append(dict_result)

    return data


def hosp_get_hosp_direction(num_dir):
    # возвращает дерево направлений-отделений, у к-рых тип улуги только is_hosp
    # [{'direction': номер направления, 'research_title': значение}, {'direction': номер направления, 'research_title': значение}]
    root_dir = tree_directions.root_direction(num_dir)
    if not root_dir or not root_dir[-1]:
        return {}
    num_root_dir = root_dir[-1][-3]
    result = tree_directions.get_research_by_dir(num_root_dir)
    num_iss = result[0][0]

    # отсортировать по подчинениям - построить бинарное дерево
    tree_dir = tree_directions.hosp_tree_direction(num_iss)
    final_tree = {}

    node_dir = Node({'order': '-1', 'direction': '', 'research_title': '', 'correct_level': True, 'color': '', 'cancel': False, 'issledovaniye': '', 'parent_iss': ''})
    for j in tree_dir:
        research_title = j[12] if j[12] else j[9]
        temp_s = {'order': '-1', 'direction': j[0], 'research_title': research_title, 'correct_level': True, 'color': '', 'cancel': j[14], 'issledovaniye': j[5], 'parent_iss': j[3]}
        if not j[3]:
            final_tree[j[5]] = Node(temp_s, parent=node_dir)
        else:
            final_tree[j[5]] = Node(temp_s, parent=final_tree.get(j[3]))

    data_sort = []
    count_level_second = 0
    correct_level = True
    for row in RenderTree(node_dir):
        order = int(len(row.pre) / 4)
        if order == 2:
            count_level_second += 1
            if count_level_second > 1:
                correct_level = False
                row.node.name['correct_level'] = correct_level
                row.node.name['color'] = 'red'
        if not correct_level and order > 2:
            row.node.name['color'] = '#d35400'
            row.node.name['correct_level'] = correct_level

        row.node.name['order'] = order
        data_sort.append(row.node.name)

    data_sort.pop(0)
    return data_sort


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


def hosp_get_text(current_iss, extract=False, mode=None, directions=None):
    # # Возврат стр-ра:
    # {'paraclinic': [{'title_research': 'Проведение электрокардиографических исследований ( ЭКГ )', 'result': [
    #                 {'date': '05.01.20 117', 'data': [{'group_title': '', 'fields': [{'title_field': 'Заключение',
    #                       'value': 'Повышение пучка Гиса'}]}]},
    #                 {'date': '05.01.20 119', 'data': [{'group_title': '', 'fields': [{'title_field': 'Заключение',
    #                       'value': 'Диффузные нарушения'}]}]}]} ]}]
    #                                                                                                                     ]}
    if directions is None:
        directions = []
    if directions:
        num_paraclinic_dirs = directions
    else:
        if mode is None:
            return {}
        num_dir = Issledovaniya.objects.get(pk=current_iss).napravleniye_id
        # получить все направления в истории по типу hosp
        hosp_dirs = hosp_get_hosp_direction(num_dir)

        # получить текущее направление типа hosp из текущего эпикриза
        current_dir = hosp_get_curent_hosp_dir(current_iss)
        if not extract:
            hosp_dirs = [i for i in hosp_dirs if i["direction"] <= current_dir]

        # получить по каждому hosp_dirs Дочерние направления по типу is_paraclinic, is_doc_refferal, is_morfology
        num_paraclinic_dirs = set()
        for h in hosp_dirs:
            obj_hosp_dirs = hosp_get_data_direction(h["direction"], site_type=-1, type_service=mode, level=2)
            if not obj_hosp_dirs:
                continue
            for k in obj_hosp_dirs:
                paraclinic_dir = k.get('direction')
                num_paraclinic_dirs.add(paraclinic_dir)

    num_paraclinic_dirs = list(num_paraclinic_dirs)

    return desc_to_data(num_paraclinic_dirs)


def desc_to_data(num_dirs: List[int], force_all_fields: bool = False):
    # [0] - заглушка для запроса. research c id =0 не бывает
    get_research_id = get_distinct_research([0], num_dirs, is_text_research=True) if num_dirs else []
    result = []
    for research_base in get_research_id:
        research = research_base[0]
        field_result = get_result_text_research(research, num_dirs, force_all_fields)
        last_group = None
        last_date = None
        data_in = []
        new_date_data = {}
        for i in field_result:
            date = f'{i[1]} {i[2]}'
            link_dicom = search_dicom_study(i[2]) if not force_all_fields else None
            group = i[3]
            if not i[5]:
                continue
            fields = {'title_field': i[4], 'value': i[5], 'field_type': i[8]}

            if date != last_date:
                if new_date_data:
                    data_in.append(new_date_data.copy())

                new_date_data = dict()
                new_date_data['date'] = date
                new_date_data['link_dicom'] = link_dicom if link_dicom else ''
                new_date_data['iss_id'] = i[6]
                new_date_data['docConfirm'] = i[7]
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
            last_fields.append(fields)
            get_last_group['fields'] = last_fields.copy()
            current_data.append(get_last_group.copy())
            new_date_data['data'] = current_data.copy()

        data_in.append(new_date_data)

        temp_result = {}
        temp_result['title_research'] = Researches.objects.get(pk=research).title
        temp_result['result'] = data_in
        result.append(temp_result)

    return result


def hosp_get_text_iss(current_iss, is_extract, mode):
    if mode is None:
        return []
    if mode == 'desc':
        modes = ['is_paraclinic', 'is_doc_refferal', 'is_morfology']
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
    if obj_iss.research.is_gistology:
        return False
    parent = Napravleniya.objects.get(pk=num_dir).parent
    if not parent and (obj_iss.research.is_doc_refferal or obj_iss.research.is_paraclinic):
        return False

    if parent:
        parent_is_hospital = parent.research.is_hospital
        if (obj_iss.research.is_doc_refferal or obj_iss.research.is_paraclinic) and not parent_is_hospital:
            return False

    hosp_nums_obj = hosp_get_hosp_direction(num_dir)
    hosp_last_num = hosp_nums_obj[-1].get('direction') if hosp_nums_obj else None
    if not hosp_last_num:
        return False
    hosp_extract = hosp_get_data_direction(hosp_last_num, site_type=7, type_service='None', level=2)
    if hosp_extract and hosp_extract[0].get('date_confirm'):
        return True

    # if not hosp_extract or not hosp_extract[0].get('date_confirm'):
    #     # Проверить подтверждение переводного эпикриза
    #     # Получить hosp_dir для текужего направления
    #     current_iss = Issledovaniya.objects.get(napravleniye_id=num_dir)
    #     current_dir_hosp_dir = num_dir
    #     if not current_iss.research.is_hospital:
    #         current_dir_hosp_dir = hosp_get_curent_hosp_dir(current_iss.pk)
    #     # получить для текущего hosp_dir эпикриз с title - перевод.....
    #     epicrisis_data = hosp_get_data_direction(current_dir_hosp_dir, site_type=6, type_service='None', level=2)
    #     if epicrisis_data:
    #         result_check = check_transfer_epicrisis(epicrisis_data)
    #         return result_check['is_transfer']
    return False


def check_transfer_epicrisis(data):
    for i in data:
        if i.get("research_title").lower().find('перевод') != -1:
            if i.get('date_confirm'):
                return {'is_transfer': True, 'iss': i.get('iss'), 'research_id': i.get('research_id')}
    return {'is_transfer': False, 'iss': None, 'research_id': None}


def get_temperature_list(hosp_num_dir):
    """
    :param num_dir:
    :return:
    {
    temperature: {data: [36.6, 36.7, 37.1 итд], xtext: ['21.01.20 13:30', '21.01.20 20:00', '22.01.20 12:10' итд],},
    systolic: {data[], xtext :[]}, diastolic: {data[], xtext :[]},
    pulse: {data[], xtext :[]}
    }
    """
    # tl - temperature list
    tl_objs = hosp_get_data_direction(hosp_num_dir, site_type=9, type_service='None', level=2)
    tl_iss = [i['iss'] for i in tl_objs]
    research_id = None
    for i in tl_objs:
        research_id = i['research_id']
        break
    if research_id is None:
        return {}
    final_data = {}
    title_list = ['Температура', 'Пульс (уд/м)', 'Дата измерения', 'Время измерения', 'Систолическое давление (мм рт.с)', 'Диастолическое давление (мм рт.с)']
    a = get_result_temperature_list(tl_iss, research_id, title_list)
    data = {}
    for i in a:
        value = i[2]
        field = i[3]
        if field.lower().find('дата') != -1:
            value = normalize_date(value)
        in_data = {field: value}
        key = i[1]
        if not data.get(key):
            data.update({key: {}})
        t_data = data.get(key)
        t_data.update(in_data)
        data[key] = t_data

    for k, v in data.items():
        date_time = get_date_time_tl(v)
        for title, value in v.items():
            if not value or value == '0':
                continue
            if not final_data.get(title):
                final_data[title] = {'data': [], 'xtext': []}
            t_final_data = final_data.get(title)
            t_data = t_final_data['data']
            t_data.append(value)
            t_xtext = t_final_data['xtext']
            t_xtext.append(date_time)
            final_data[title] = {'data': t_data, 'xtext': t_xtext}
    final_data.pop('Дата измерения', None)
    final_data.pop('Время измерения', None)
    for k, v in final_data.items():
        if 'температура' in k.lower() or 'давление' in k.lower() or 'пульс' in k.lower():
            number_data = list(map(force_to_number, v['data']))
            v['data'] = number_data
            v['min_max'] = [min(number_data), max(number_data)]
            final_data[k] = v
    if 'Температура' in final_data:
        final_data['Температура (°C)'] = final_data.pop('Температура')
    return final_data


def get_date_time_tl(dict_data):
    import re

    time = dict_data.get('Время измерения', 'Нет поля "Время измерения"')
    date = dict_data.get('Дата измерения', 'Нет поля "Дата измерения"')
    date = re.sub(r'.\d{4}', '', date)
    return f'{date} {time}'


def force_to_number(val):
    return float(''.join(c for c in val if c.isdigit() or c == '.') or 0)


def get_assignments(direction_id: int):
    if direction_id is None:
        return []
    results = []
    issledovanie_id = Issledovaniya.objects.get(napravleniye_id=direction_id).pk
    assignments = get_assignments_by_history(issledovanie_id)
    prev_directions_id = -1
    for i in assignments:
        if prev_directions_id != i.napravlenie_id:
            who_assigned = i.who_assigned.split(" ")
            family_assigned = who_assigned[0]
            name_assigned = who_assigned[1][0]
            patronymic_assigned = ""
            if len(who_assigned) > 2:
                patronymic_assigned = who_assigned[2][0]
            tmp_res = {
                "direction_id": i.napravlenie_id,
                "research_id": [i.research_id],
                "research_title": [f"{i.research_title}; "],
                "create_date": i.data_sozdaniya.strftime("%d.%m.%Y"),
                "who_assigned": f"{family_assigned} {name_assigned}.{patronymic_assigned}.",
                "time_confirmation": "",
                "who_confirm": "",
            }
            if i.total_confirmed:
                who_confirm = i.who_confirm.split(" ")
                family_confirm = who_confirm[0]
                name_confirm = who_confirm[1][0]
                patronymic_confirm = ""
                if len(who_confirm) > 2:
                    patronymic_confirm = who_confirm[2][0]
                tmp_res["time_confirmation"] = i.time_confirmation.strftime("%d.%m.%Y %H:%M")
                tmp_res["who_confirm"] = f"{family_confirm} {name_confirm}.{patronymic_confirm}."
            results.append(tmp_res)
        else:
            results[-1]["research_id"].append(i.research_id)
            results[-1]["research_title"].append(f"{i.research_title}; ")
        prev_directions_id = i.napravlenie_id
    return results
