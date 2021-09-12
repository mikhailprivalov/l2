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
            print("json", i)
        else:
            tmp_data[i.title] = i.value
        prev_issledovaniye_id = i.issledovaniye_id
        count += 1
    data_return.append(deepcopy(tmp_data))
    return data_return


def death_split_diag(data, data_return, type):
    item = None
    if "а)" in type:
        item = "а"
    elif "б)" in type:
        item = "б"
    elif "в)" in type:
        item = "в"

    if item:
        diag = f"{data['rows'][0][2]}".split(" ")
        diag_text, diag_mkb = "", ""
        if diag[0]:
            diag_mkb = diag.pop(0)
            diag_text = ' '.join(diag)
        data_return[f"{type}_период"] = f"{data['rows'][0][0]} {data['rows'][0][1]}"
        data_return[f"{type}_диагноз_мкб"] = diag_mkb
        data_return[f"{type}_диагноз_текст"] = diag_text
    return data_return
