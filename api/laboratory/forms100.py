def form_01(request_data):
    file = request_data.get("file")
    issledovanie_id = request_data.get("entity_id")
    file = request_data.get("file")
    print(file)
    print(issledovanie_id)
    return {"ok": True, "result": [], "message": ""}
