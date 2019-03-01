def get_all_doc(ind_doc):
    """
    возвращает словарь словарей documents. Данные о документах: паспорт : номер: серия, полис: номер, снислс: номер
    """
    documents = {'passport': {'num': "", 'serial': "", 'date_start': "", 'issued': ""},
                 'polis': {'serial': "", 'num': "", 'issued': ""},
                 'snils': {'num':""}
                 }

    ind_doc_l=ind_doc

    for z in range(len(ind_doc_l)):
        if ind_doc_l[z].get('document_type') == 1:
            documents['passport']['num'] = ind_doc_l[z].get('number')
            documents['passport']['serial'] = ind_doc_l[z].get('serial')
            if ind_doc_l[z].get('date_start'):
                documents['passport']['date_start'] = ind_doc_l[z].get('date_start')
        if ind_doc_l[z].get('document_type') == 3:
            if len(ind_doc_l[z].get('number')) == 16:
                documents['polis']['num'] = ind_doc[z].get('number')
        if ind_doc_l[z].get('document_type') == 4:
            documents['snils']['num'] = ind_doc_l[z].get('number')

    return documents


def get_card_attr(ind_card):
    """
    Возвращает словарь card_attr. Атрибуты карт пациента: номер карты и тип(несколько),address, phone (несколько)
    """
    card_attr = {'num_type':{},
                 'phone':"",
                 'addr':"",
                 }

    ind_card_l=ind_card

    for z in range(len(ind_card_l)):
        card_attr['num_type'][ind_card_l[z].number] = ind_card_l[z].base.title
        card_attr['phone']= ind_card_l[z].get_phones()
        if ind_card_l[z].base.is_rmis:
            card_attr['addr'] = ind_card_l[z].main_address

    return card_attr