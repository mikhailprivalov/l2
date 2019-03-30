from clients.models import Document
from directions.models import Napravleniya, IstochnikiFinansirovaniya, Issledovaniya
from directory.models import Researches


def get_all_doc(docs: [Document]):
    """
    возвращает словарь словарей documents. Данные о документах: паспорт : номер: серия, полис: номер, снислс: номер
    """
    documents = {
        'passport': {'num': "", 'serial': "", 'date_start': "", 'issued': ""},
        'polis': {'serial': "", 'num': "", 'issued': ""},
        'snils': {'num': ""}
    }

    for d in docs:
        if d.document_type.title == "СНИЛС":
            documents["snils"]["num"] = d.number

        if d.document_type.title == 'Паспорт гражданина РФ':
            documents["passport"]["num"] = d.number
            documents["passport"]["serial"] = d.serial
            documents["passport"]["date_start"] = "" if not d.date_start else d.date_start.strftime("%d.%m.%Y")
            documents["polis"]["issued"] = d.who_give

        if d.document_type.title == 'Полис ОМС':
            documents["polis"]["num"] = d.number
            documents["polis"]["serial"] = d.serial
            documents["polis"]["date_start"] = "" if not d.date_start else d.date_start.strftime("%d.%m.%Y")
            documents["polis"]["issued"] = d.who_give

    return documents


# def get_card_attr(ind_card_l):
#     """
#     Возвращает словарь card_attr. Атрибуты карт пациента: номер карты и тип(несколько),address, phone (несколько)
#     """
#     card_attr = {'num_type': {},
#                  'phone': "",
#                  'addr': "",
#                  }
#
#
#     for z in range(len(ind_card_l)):
#         card_attr['num_type'][ind_card_l[z].number] = ind_card_l[z].base.title
#         card_attr['phone']= ind_card_l[z].get_phones()
#         if ind_card_l[z].base.is_rmis:
#             card_attr['addr'] = ind_card_l[z].main_address
#
#     return card_attr

def get_coast_from_issledovanie(dir_research_loc):
    """
    При печати листа на оплату возвращает (цены из записанных в Исследования)
    На основании прайса, услуг возвращает Для листа на оплату {
                                                             направление: {услуга:[цена, скидка, количество],услуга:[цена, скидка, количество]},
                                                             направление: {услуга:[цена, скидка, количество],услуга:[цена, скидка, количество]},
                                                             направление: {услуга:[цена, скидка, количество],услуга:[цена, скидка, количество]},
                                                             }
    """
    d = tuple()
    if type(dir_research_loc) == dict:
        dict_coast = {}
        for k, v in dir_research_loc.items():
            d = ({r: [s, d, h, ] for r, s, d, h in
                  Issledovaniya.objects.filter(napravleniye=k, research__in=v, coast__isnull=False).values_list(
                      'research_id', 'coast', 'discount', 'how_many')})
            dict_coast[k] = d
        return dict_coast
    else:
        return 0


def get_research_by_dir(dir_temp_l):
    """
    Получить словаь: {направление1:[услуга1, услуга2, услуга3],направление2:[услуга1].....}
    :param dir_temp_l:
    :return:
    """
    dict_research_dir = {}
    for i in dir_temp_l:
        # Если есть хотя бы одно сохранения услуги по направлению, то не учитывается
        if any([x.doc_save is not None for x in Issledovaniya.objects.filter(napravleniye=i)]):
            continue
        else:
            research_l = ([x.research_id for x in Issledovaniya.objects.filter(napravleniye=i)])
        dict_research_dir[i] = research_l
    return dict_research_dir


def get_final_data(research_price_loc):
    """
    Получить итоговую структуру данных: код услуги, напрвление, услуга, цена, скидка/наценка, цена со скидкой, кол-во, сумма

    Направление указывается один раз для нескольких строк
    """

    total_sum = 0
    tmp_data = []
    is_discount = False
    z = ""
    x = ""
    tmp_napr = []
    for k, v in research_price_loc.items():
        research_attr = ([s for s in Researches.objects.filter(id__in=v.keys()).values_list('id', 'title')])
        research_attr_list = [list(z) for z in research_attr]
        for research_id, research_coast in v.items():
            h = []
            for j in research_attr_list:
                if research_id == j[0]:
                    if k != 0:
                        h.append(k)
                        k = 0
                    else:
                        h.append("")
                    h.extend(j)
                    h.append("{:,.2f}".format(research_coast[0]).replace(",", " "))
                    coast_with_discount = research_coast[0] + (research_coast[0] * research_coast[1] / 100)
                    if research_coast[1] != 0:
                        z = "+"
                        if research_coast[1] > 0:
                            x = "+"
                        else:
                            x = ""
                        h.append(x + str(research_coast[1]))
                        h.append("{:,.2f}".format(coast_with_discount).replace(",", " "))
                    h.append(research_coast[2])
                    research_sum = coast_with_discount * research_coast[2]
                    h.append("{:,.2f}".format(research_sum).replace(",", " "))
                    h[0], h[1] = h[1], h[0]
                    total_sum += research_sum
                    research_attr_list.remove(j)
                    tmp_data.append(h)
                    if h[1]:
                        tmp_napr.append(h[1])
                if h:
                    break

    res_lis = []
    for t in tmp_data:
        tmp_d = list(map(str, t))
        res_lis.append(tmp_d)

    total_data = []

    total_data.append(res_lis)

    total_data.append("{:,.2f}".format(total_sum).replace(",", " "))
    if z == "+":
        total_data.append("is_discount")
    else:
        total_data.append("no_discount")

    total_data.append(tmp_napr)

    # total_data:[стру-рка данных, итоговая сумма, есть ли скидка, номера направлений]

    return total_data


def form_notfound():
    """
    В случае не верной настройки форм по типам и функциям или переданным аргументам в параметры
    :return:
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from copy import deepcopy
    from reportlab.lib.enums import TA_CENTER
    import os.path
    from io import BytesIO
    from laboratory.settings import FONTS_FOLDER

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=10 * mm,
                            rightMargin=10 * mm, topMargin=10 * mm,
                            bottomMargin=10 * mm, allowSplitting=1,
                            title="Форма {}".format("Паспорт здоровья"))
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifBold"
    style.fontSize = 16
    style.leading = 15
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER

    objs = [
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">Ая-я-я-я-я-я-я-яй!</font>',
                  styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">Что-то Администраторы не верно настроили с типами форм! </font>',
                  styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">А-та-та-та им!</font>',
                  styleCenter),
    ]
    doc.build(objs)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf
