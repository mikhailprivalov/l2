import os.path
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from api.gardening.views import (
    _contribution_payment_types,
    _contribution_row,
    _electricity_result,
    _list_bank_receipts,
)
from directory.models import OwnersRealEstate, RealEstate
from laboratory.settings import FONTS_FOLDER


def _format_date(value):
    if not value:
        return "—"
    if isinstance(value, str):
        parts = value.split("-")
        if len(parts) >= 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
        return value
    return value.strftime("%d.%m.%Y")


def _fio(owner):
    individual = owner.individual
    if not individual:
        return ""
    parts = [individual.family or "", individual.name or "", individual.patronymic or ""]
    return " ".join(part.strip() for part in parts if part and part.strip())


def _dash(value):
    if value in (None, ""):
        return "—"
    return str(value)


def _pdf_amount(raw):
    if raw in (None, ""):
        return None
    try:
        return Decimal(str(raw).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _pdf_sum(rows, key):
    total = Decimal("0")
    any_val = False
    for row in rows:
        amount = _pdf_amount(row.get(key))
        if amount is None:
            continue
        total += amount
        any_val = True
    if not any_val:
        return "—"
    return f"{total:.2f}"


def _owners_for_year(real_estate, year):
    year_start = date(int(year), 1, 1)
    year_end = date(int(year), 12, 31)
    result = []
    for owner in OwnersRealEstate.objects.select_related("individual").filter(real_estate=real_estate, hide=False).order_by("date_start", "pk"):
        start = owner.date_start or date.min
        end = owner.date_end or date.max
        if start <= year_end and end >= year_start:
            result.append(owner)
    return result


def _header_owner(owners):
    if not owners:
        return None
    open_owners = [item for item in owners if item.date_end is None]
    pool = open_owners or owners
    return max(pool, key=lambda item: (item.date_start or date.min, item.pk))


def _calc_mode_label(payment_type):
    if getattr(payment_type, "is_use_kilowatt", False):
        return "кВт энергии"
    if getattr(payment_type, "is_by_area", False):
        return "Площадь участка"
    if getattr(payment_type, "is_absolute", False):
        return "Абсолютная сумма"
    return ""


def _contribution_pdf_title(payment_type):
    title = (payment_type.title or "").strip() or "—"
    mode = _calc_mode_label(payment_type)
    if mode:
        return f"{title} ({mode})"
    return title


def _pdf_missing_zero(raw, ok_style, missing_style):
    if raw in (None, ""):
        return _p("0.00", missing_style)
    return _p(raw, ok_style)


def _p(text, style):
    return Paragraph(str(text if text not in (None, "") else "—"), style)


def form_01(request_data):
    """
    Садоводство — карточка участка: владелец, приходы, взносы, показания электроэнергии.
    type=115.01&real_estate_id=&year=
    """
    pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))

    style_sheet = getSampleStyleSheet()
    style = style_sheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 10
    style.alignment = TA_LEFT

    style_bold = deepcopy(style)
    style_bold.fontName = "PTAstraSerifBold"
    style_bold.fontSize = 11
    style_bold.leading = 14

    style_title = deepcopy(style_bold)
    style_title.fontSize = 12
    style_title.alignment = TA_LEFT

    style_section = deepcopy(style_bold)
    style_section.fontSize = 9
    style_section.spaceBefore = 2 * mm
    style_section.spaceAfter = 1 * mm

    style_th = deepcopy(style_bold)
    style_th.fontSize = 9
    style_th.leading = 9
    style_th.alignment = TA_CENTER

    style_td = deepcopy(style)
    style_td.fontSize = 9
    style_td.leading = 9

    style_td_right = deepcopy(style_td)
    style_td_right.alignment = TA_RIGHT

    style_th_right = deepcopy(style_bold)
    style_th_right.fontSize = 9
    style_th_right.leading = 9
    style_th_right.alignment = TA_RIGHT

    style_td_red = deepcopy(style_td_right)
    style_td_red.textColor = colors.HexColor("#c62828")
    style_td_red.fontName = "PTAstraSerifBold"

    style_td_bold = deepcopy(style_td)
    style_td_bold.fontName = "PTAstraSerifBold"

    style_td_right_bold = deepcopy(style_td_right)
    style_td_right_bold.fontName = "PTAstraSerifBold"

    style_td_red_bold = deepcopy(style_td_red)
    style_td_red_bold.fontName = "PTAstraSerifBold"

    style_empty = deepcopy(style)
    style_empty.fontSize = 9

    real_estate_id = request_data.get("real_estate_id") or request_data.get("id")
    year_raw = request_data.get("year")
    try:
        year = int(year_raw)
    except (TypeError, ValueError):
        year = None

    buffer = BytesIO()
    page = landscape(A4)
    table_width = page[0] - 20 * mm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title="Участок садоводства",
    )
    objs = []

    real_estate = RealEstate.objects.filter(pk=real_estate_id, hide=False).first() if real_estate_id else None
    if not real_estate or year is None:
        objs.append(Paragraph("Не указан объект или год", style_empty))
        doc.build(objs)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    owners = _owners_for_year(real_estate, year)
    fios = ", ".join(name for name in (_fio(item) for item in owners) if name) or "—"
    header_owner = _header_owner(owners)
    date_start = _format_date(header_owner.date_start if header_owner else None)
    date_end = _format_date(header_owner.date_end if header_owner else None)
    plot_no = real_estate.num_object if real_estate.num_object is not None else "—"
    header = f"№ {plot_no} — {fios} за {year} {date_start} — {date_end}"
    objs.append(Paragraph(header, style_title))
    objs.append(Spacer(1, 4 * mm))

    objs.append(Paragraph("Приходы", style_section))
    receipts = _list_bank_receipts(real_estate, year)
    receipt_data = [
        [
            _p("Дата", style_th),
            _p("Вид платежа", style_th),
            _p("Сумма", style_th),
            _p("Комментарий", style_th),
        ]
    ]
    total = Decimal("0")
    for item in receipts:
        receipt_data.append(
            [
                _p(_format_date(item.get("date")), style_td),
                _p(item.get("payment_type_title") or "—", style_td),
                _p(_dash(item.get("amount")), style_td_right),
                _p(item.get("comment") or "—", style_td),
            ]
        )
        try:
            total += Decimal(str(item.get("amount") or "0"))
        except (InvalidOperation, TypeError, ValueError):
            pass
        for child in item.get("parent_pay_receipt") or []:
            receipt_data.append(
                [
                    _p(_format_date(child.get("date")), style_td),
                    _p(f"– {child.get('payment_type_title') or '—'}", style_td),
                    _p(_dash(child.get("amount")), style_td_right),
                    _p(child.get("comment") or "—", style_td),
                ]
            )
    if len(receipt_data) == 1:
        receipt_data.append(
            [
                _p("Нет поступлений", style_td),
                _p("", style_td),
                _p("", style_td),
                _p("", style_td),
            ]
        )
    else:
        receipt_data.append(
            [
                _p("Итого", style_th_right),
                _p("", style_td),
                _p(f"{total.quantize(Decimal('0.01'))}", style_th_right),
                _p("", style_td),
            ]
        )

    receipt_table_style = [
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b1b1b1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ececec")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if len(receipt_data) > 2:
        receipt_table_style.extend(
            [
                ("SPAN", (0, -1), (1, -1)),
                ("ALIGN", (0, -1), (2, -1), "RIGHT"),
            ]
        )
    receipt_table = Table(receipt_data, colWidths=[28 * mm, 90 * mm, 30 * mm, table_width - 148 * mm], repeatRows=1)
    receipt_table.hAlign = "LEFT"
    receipt_table.setStyle(TableStyle(receipt_table_style))
    objs.append(receipt_table)
    objs.append(Spacer(1, 5 * mm))

    objs.append(Paragraph("Взносы", style_section))
    payment_types = _contribution_payment_types(year)
    contrib_data = [
        [
            _p("Взнос", style_th),
            _p("Тариф", style_th),
            _p("Коэффициент", style_th),
            _p("Начислено", style_th),
            _p("Списано", style_th),
            _p("Долг", style_th),
            _p("Остаток", style_th),
        ]
    ]
    if not payment_types:
        contrib_data.append(
            [
                _p("Нет взносов", style_td),
                _p("", style_td),
                _p("", style_td),
                _p("", style_td),
                _p("", style_td),
                _p("", style_td),
                _p("", style_td),
            ]
        )
    else:
        for payment_type in payment_types:
            row = _contribution_row(real_estate, payment_type, year)
            debt_amount = _pdf_amount(row.get("debt"))
            debt_style = style_td_red if debt_amount is not None and debt_amount > 0 else style_td_right
            contrib_data.append(
                [
                    _p(_contribution_pdf_title(payment_type), style_td),
                    _pdf_missing_zero(row.get("tariff"), style_td_right, style_td_red),
                    _pdf_missing_zero(row.get("coefficient"), style_td_right, style_td_red),
                    _pdf_missing_zero(row.get("charge"), style_td_right, style_td_red),
                    _p(_dash(row.get("written_off")), style_td_right),
                    _p(_dash(row.get("debt")), debt_style),
                    _p(_dash(row.get("remainder")), style_td_right),
                ]
            )
    contrib_widths = [70 * mm, 28 * mm, 32 * mm, 30 * mm, 28 * mm, 26 * mm]
    contrib_widths.append(table_width - sum(contrib_widths))
    contrib_table = Table(contrib_data, colWidths=contrib_widths, repeatRows=1)
    contrib_table.hAlign = "LEFT"
    contrib_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b1b1b1")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ececec")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    objs.append(contrib_table)
    objs.append(Spacer(1, 5 * mm))

    objs.append(Paragraph("Показания электроэнергии", style_section))
    electricity = _electricity_result(real_estate, year)
    meters = electricity.get("meters") or []
    if not meters and electricity.get("rows"):
        meters = [{"title": "Счётчик 1", "show_money": True, "rows": electricity.get("rows")}]
    show_meter_col = len(meters) > 1
    elec_headers = ["Месяц"]
    if show_meter_col:
        elec_headers.append("Счётчик")
    elec_headers.extend(["Предыдущий", "Текущий", "Потребление", "Тариф", "Начислено", "Списано", "Долг", "Остаток", "Приход"])
    elec_data = [[_p(title, style_th) for title in elec_headers]]
    total_row_indexes = []
    for month in range(1, 13):
        month_entries = []
        for meter in meters:
            row = next((item for item in (meter.get("rows") or []) if item.get("month") == month), None)
            if row:
                month_entries.append((meter, row))
        has_total = len(month_entries) > 1
        for meter, row in month_entries:
            show_money = (not has_total) and row.get("remainder") is not None
            tariff_missing = row.get("tariff") in (None, "")
            debt_raw = row.get("debt") if show_money else None
            debt_amount = _pdf_amount(debt_raw)
            debt_style = style_td_red if debt_amount is not None and debt_amount > 0 else style_td_right
            cells = [_p(row.get("month_label") or "—", style_td)]
            if show_meter_col:
                cells.append(_p(meter.get("title") or "—", style_td))
            cells.extend(
                [
                    _p(_dash(row.get("previous_reading")), style_td_right),
                    _p(_dash(row.get("current_reading")), style_td_right),
                    _p(_dash(row.get("consumption")), style_td_right),
                    _p("0.00" if tariff_missing else row.get("tariff"), style_td_red if tariff_missing else style_td_right),
                    _p(_dash(row.get("charge")), style_td_right),
                    _p(_dash(row.get("written_off")), style_td_right),
                    _p(_dash(row.get("debt")) if show_money else "—", debt_style),
                    _p(_dash(row.get("remainder")) if show_money else "—", style_td_right),
                    _p(_dash(row.get("receipt")) if show_money else "—", style_td_right),
                ]
            )
            elec_data.append(cells)
        if has_total:
            month_rows = [row for _meter, row in month_entries]
            money_row = next((row for row in month_rows if row.get("remainder") is not None), month_rows[0])
            debt_amount = _pdf_amount(money_row.get("debt"))
            debt_style = style_td_red_bold if debt_amount is not None and debt_amount > 0 else style_td_right_bold
            cells = [_p("", style_td_bold)]
            if show_meter_col:
                cells.append(_p("Итого", style_td_bold))
            cells.extend(
                [
                    _p("—", style_td_right_bold),
                    _p("—", style_td_right_bold),
                    _p(_pdf_sum(month_rows, "consumption"), style_td_right_bold),
                    _p("—", style_td_right_bold),
                    _p(_pdf_sum(month_rows, "charge"), style_td_right_bold),
                    _p(_pdf_sum(month_rows, "written_off"), style_td_right_bold),
                    _p(_dash(money_row.get("debt")), debt_style),
                    _p(_dash(money_row.get("remainder")), style_td_right_bold),
                    _p(_dash(money_row.get("receipt")), style_td_right_bold),
                ]
            )
            elec_data.append(cells)
            total_row_indexes.append(len(elec_data) - 1)
    if show_meter_col:
        col_w = [22 * mm, 32 * mm, 22 * mm, 22 * mm, 24 * mm, 20 * mm, 24 * mm, 22 * mm, 20 * mm, 24 * mm]
    else:
        col_w = [24 * mm, 26 * mm, 24 * mm, 26 * mm, 22 * mm, 26 * mm, 24 * mm, 22 * mm, 26 * mm]
    col_w.append(table_width - sum(col_w))
    elec_table = Table(elec_data, colWidths=col_w, repeatRows=1)
    elec_table.hAlign = "LEFT"
    elec_style = [
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b1b1b1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ececec")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]
    for idx in total_row_indexes:
        elec_style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#ececec")))
    elec_table.setStyle(TableStyle(elec_style))
    objs.append(elec_table)

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
