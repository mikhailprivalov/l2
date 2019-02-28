def get_all_doc(ind_doc):
    """
    возвращает номера документов documents
    :param kwargs:
    :return:
    """
    ind_doc=ind_doc
    document_passport_num = ""
    document_passport_serial=""
    document_passport_date_start=""
    document_polis=""
    document_snils=""
    documents=['','','','','']
    for z in range(len(ind_doc)):
        if ind_doc[z].get('document_type') == 1:
            document_passport_num = ind_doc[z].get('number')
            document_passport_serial = ind_doc[z].get('serial')
            documents.insert(0,document_passport_num)
            documents.insert(1,document_passport_serial)
            if ind_doc[z].get('date_start'):
                document_passport_date_start = ind_doc[z].get('date_start')
                documents.insert(2,document_passport_date_start)
        if ind_doc[z].get('document_type') == 3:
            if len(ind_doc[z].get('number')) == 16:
                document_polis = ind_doc[z].get('number')
                documents.insert(3, document_polis)
        if ind_doc[z].get('document_type') == 4:
            document_snils = ind_doc[z].get('number')
            documents.insert(4,document_snils)

    return documents

def get_cards_attr(ind_card):
    """
    возвращает в данном порядке: 0-карты(номер-тип), 1-адрес регистрации, 2-один телефон
    :return:
    """
    ind_card=ind_card
    ind_card_s = ""
    phone_card = []
    card_attr =['','','']

    for z in range(len(ind_card)):
        ind_card_s += ind_card[z].number +'(' + ind_card[z].base.title+')'+'&nbsp;&nbsp;&nbsp;'
        phone_card=ind_card[z].get_phones()
        if ind_card[z].base.is_rmis:
            address_card = ind_card[z].main_address
    if phone_card:
        card_attr.insert(2,phone_card[0])

    card_attr.insert(0,ind_card_s)
    card_attr.insert(1,address_card)

    return card_attr