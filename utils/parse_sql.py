from copy import deepcopy


def death_form_result_parse(data):
    tmp_data = {}
    data_return = []
    count = 0
    prev_issledovaniye_id = None
    for i in data:
        if i.issledovaniye_id != prev_issledovaniye_id and count > 0:
            data_return.append(deepcopy(tmp_data))
            tmp_data = {}
        if i.json_value:
            tmp_data[i.title] = i.json_value
        else:
            tmp_data[i.title] = i.value
        prev_issledovaniye_id = i.issledovaniye_id
        count += 1
    data_return.append(deepcopy(tmp_data))
    return data_return
