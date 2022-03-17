def dispanserization_data(query_sql, pk_service_start, pk_service_end):
    dates = [i.confirm_time for i in query_sql]
    dates = sorted(set(dates))
    print(list(dates))
    dates_val = [{"val_start": 0, "val_end": 0} for i in range(len(dates))]
    result = []
    prev_doc = None
    step = 0
    current_tmp_data = {}
    for i in query_sql:
        current_index = dates.index(i.confirm_time)
        if i.doc_confirmation_id != prev_doc:
            if step != 0:
                result.append(current_tmp_data.copy())
            current_doc = {"fio_doc": i.fio_doctor, "dates": dates.copy(), "dates_val": dates_val.copy()}
            tmp_val = current_doc.get("dates_val", [])[current_index]
            if i.research_id in pk_service_start:
                tmp_val["val_start"] += 1
            else:
                tmp_val["val_end"] += 1
            current_doc["dates_val"][current_index] = tmp_val.copy()
            current_tmp_data = {i.doc_confirmation_id: current_doc.copy()}

        current_doc = current_tmp_data.get(i.doc_confirmation_id)
        tmp_val = current_doc.get("dates_val", [])[current_index]
        if i.research_id in pk_service_start:
            tmp_val["val_start"] += 1
        else:
            tmp_val["val_end"] += 1
        current_doc.get("dates_val", [])[current_index] = tmp_val.copy()
        current_tmp_data = {i.doc_confirmation_id: current_doc.copy()}
        prev_doc = i.doc_confirmation_id
        step += 1
    result.append(current_tmp_data.copy())
    print(result)

    return result

