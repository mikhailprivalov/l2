def _value(row, name):
    if isinstance(row, dict):
        return row[name]
    return getattr(row, name)


def aggregate_approval_rows(rows):
    documents = {}
    order = []
    for row in rows:
        document_id = _value(row, "document_id")
        if document_id not in documents:
            documents[document_id] = {
                "documentId": document_id,
                "hospitalId": _value(row, "hospital_id"),
                "hospital": _value(row, "hospital_title") or "",
                "confirmAt": _value(row, "time_confirmation"),
                "approvable": 0,
                "approvedCount": 0,
            }
            order.append(document_id)
        item = documents[document_id]
        confirmed_at = _value(row, "time_confirmation")
        if item["confirmAt"] is None or (confirmed_at is not None and confirmed_at >= item["confirmAt"]):
            item["confirmAt"] = confirmed_at
            item["hospitalId"] = _value(row, "hospital_id")
            item["hospital"] = _value(row, "hospital_title") or ""
        if _value(row, "curator_field_id"):
            item["approvable"] += 1
            if _value(row, "approved"):
                item["approvedCount"] += 1
    result = []
    for document_id in order:
        item = documents[document_id]
        result.append(
            {
                "documentId": item["documentId"],
                "hospitalId": item["hospitalId"],
                "hospital": item["hospital"],
                "confirmAt": item["confirmAt"],
                "approved": item["approvable"] > 0 and item["approvedCount"] == item["approvable"],
            }
        )
    result.sort(key=lambda row: ((row["hospital"] or "").casefold(), row["documentId"]))
    return result
