
def form_01(request_data):
    """
    На входе:
    Файл XLSX с ценами прайса
    Cтруктура:
    Код по прайсу (internal_code Researches, Услуга (title_researches), следующее поле - любое текстовое название прайса
    """
    file = request_data.get("file")
    selected_form = request_data.get("selectedForm")
    entity_id = request_data.get("entityId")
    other_need_data = request_data.get("otherNeedData")
    user = request_data.get('user')
    hospital = request_data.get('hospital')

    return []
