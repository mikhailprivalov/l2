def check_need_col(cols: list, need_cols: set):
    missing_cols = need_cols - set(cols)
    if missing_cols:
        return {"ok": False, "message": f"Нет обязательных полей: {', '.join(missing_cols)}"}
    return {"ok": True, "message": "", "result": ""}
