import ast
import re

import simplejson as json
from django.http import HttpRequest
from django.utils.html import escape

from utils.dates import normalize_date


EPICRIZIS_START_TITLE = "Выписной эпикриз из медицинской карты стационарного больного."

_TABLE_STYLE = "width:100%;border-collapse:collapse;border:1px solid #000"
_CELL_STYLE = "border:1px solid #000;padding:2px 4px;vertical-align:top"


def _is_epicrisis_start(title):
    title = (title or "").strip()
    return title == EPICRIZIS_START_TITLE or title.startswith(EPICRIZIS_START_TITLE)


def fetch_paraclinic_form_data(user, params):
    from api.directions.views import directions_paraclinic_form

    internal_request = HttpRequest()
    internal_request.method = "POST"
    internal_request.user = user
    internal_request._body = json.dumps(params).encode("utf-8")

    response = directions_paraclinic_form(internal_request)
    try:
        data = json.loads(response.content.decode("utf-8"))
    except Exception:
        return None, "Ошибка разбора данных параклинической формы"

    if not data.get("ok"):
        return None, data.get("message") or "Не удалось получить данные параклинической формы"
    return data, None


def _is_code_title_dict(data):
    if not isinstance(data, dict):
        return False
    if "rows" in data or "columns" in data:
        return False
    return "code" in data or "title" in data


def _parse_code_title_object(value):
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        return value if _is_code_title_dict(value) else None

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()
    if not value.startswith("{"):
        return None

    for candidate in (value, value.replace("'", '"')):
        try:
            data = json.loads(candidate)
            if isinstance(data, str):
                data = json.loads(data)
            if _is_code_title_dict(data):
                return data
        except Exception:
            pass

    try:
        data = ast.literal_eval(value)
        if _is_code_title_dict(data):
            return data
    except Exception:
        pass

    code_match = re.search(r'["\']code["\']\s*:\s*["\']([^"\']*)["\']', value)
    title_match = re.search(r'["\']title["\']\s*:\s*["\']((?:[^"\\]|\\.)*)["\']', value)
    if code_match or title_match:
        return {
            "code": code_match.group(1) if code_match else "",
            "title": title_match.group(1) if title_match else "",
        }

    return None


def _format_code_title_value(value):
    data = _parse_code_title_object(value)
    if not data:
        return None

    code = str(data.get("code", "") or "").strip()
    title = str(data.get("title", "") or "").strip()
    if code and title:
        return f"{code} - {title}"
    return title or code or None


def _format_date_value(value):
    if value in (None, ""):
        return value

    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        date_part = text[:10]
        date_chunks = date_part.split("-")
        if len(date_chunks) == 3 and all(part.isdigit() for part in date_chunks):
            formatted_date = normalize_date(date_part)
            if len(text) > 10:
                return f"{formatted_date}{text[10:]}"
            return formatted_date
    return text


def _display_text_value(value):
    formatted = _format_code_title_value(value)
    if formatted is not None:
        return escape(formatted)
    return escape(_format_date_value(value)).replace("\n", "<br>")


def _is_table_field_data(data):
    return isinstance(data, dict) and ("rows" in data or "columns" in data)


def _table_cell_has_value(cell):
    if cell is None or cell == "":
        return False
    if isinstance(cell, str):
        stripped = cell.strip()
        if not stripped:
            return False
        formatted = _format_code_title_value(cell)
        return bool(str(formatted).strip()) if formatted is not None else True
    formatted = _format_code_title_value(cell)
    if formatted is not None:
        return bool(str(formatted).strip())
    if isinstance(cell, (list, tuple)):
        return any(_table_cell_has_value(item) for item in cell)
    if isinstance(cell, dict):
        return any(_table_cell_has_value(item) for item in cell.values())
    return bool(str(cell).strip())


def _table_rows_have_values(rows):
    if not rows:
        return False
    for row in rows:
        if not isinstance(row, list):
            continue
        if any(_table_cell_has_value(cell) for cell in row):
            return True
    return False


def _format_table_field(field):
    value = field.get("value")
    if not value:
        return ""

    try:
        table_data = json.loads(value) if isinstance(value, str) else value
    except Exception:
        return escape(str(value))

    if not _is_table_field_data(table_data):
        return escape(str(value))

    rows = table_data.get("rows") or []
    if not _table_rows_have_values(rows):
        return ""

    columns = []
    columns_data = table_data.get("columns") or {}
    if isinstance(columns_data, dict):
        columns = columns_data.get("titles") or []

    control_param = field.get("controlParam") or ""
    if not columns and control_param:
        try:
            params = json.loads(control_param)
            columns = params.get("columns", {}).get("titles", [])
        except Exception:
            columns = []

    if not columns and rows and rows[0]:
        columns = [f"Колонка {idx + 1}" for idx in range(len(rows[0]))]

    header = "".join(f'<th style="{_CELL_STYLE}">{escape(str(title))}</th>' for title in columns)
    body_rows = []
    for row in rows:
        if not isinstance(row, list):
            continue
        cells = "".join(f'<td style="{_CELL_STYLE}">{_display_text_value(cell)}</td>' for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")

    if not body_rows:
        return ""

    return f'<table style="{_TABLE_STYLE}"><thead><tr>{header}</tr></thead><tbody>{"".join(body_rows)}</tbody></table>'


def _is_empty_directions_value(value):
    if value in (None, "", "[]"):
        return True
    try:
        data = json.loads(value) if isinstance(value, str) else value
    except Exception:
        return False
    if not isinstance(data, dict) or "directions" not in data:
        return False
    if data.get("directions"):
        return False
    excluded = data.get("excluded")
    if excluded is None:
        return True
    if isinstance(excluded, list):
        return len(excluded) == 0
    if isinstance(excluded, dict):
        return not any(excluded.values())
    return False


def _format_field_display(field):
    if field.get("hide"):
        return None, False

    field_type = field.get("field_type")
    value = field.get("value")

    if field_type == 42:
        files = field.get("files") or []
        if not files:
            return None, False
        file_names = ", ".join(escape(file_item.get("originalName", "")) for file_item in files if file_item.get("originalName"))
        return file_names or None, False

    if _is_empty_directions_value(value):
        return None, False

    if value in (None, "") and field_type != 42:
        return None, False

    if field_type in (2, 28, 32, 33, 34):
        formatted = _format_code_title_value(value)
        if formatted is not None:
            return escape(formatted), False

    if field_type == 1:
        return escape(_format_date_value(value)), False

    if field_type == 15:
        return value or "", True

    if field_type == 24:
        table = _render_laboratory_results_table(value)
        if table:
            return table, True

    if field_type in (25, 26):
        table = _render_doc_referral_results_table(value)
        if table:
            return table, True

    if field_type == 38:
        table = _render_procedure_list_table(value)
        if table:
            return table, True

    if field_type == 27:
        return _format_table_field(field), False

    if field_type == 44:
        try:
            items = json.loads(value) if isinstance(value, str) else value
            if isinstance(items, list):
                formatted_items = []
                for item in items:
                    if item in (None, ""):
                        continue
                    item_formatted = _format_code_title_value(item)
                    formatted_items.append(escape(item_formatted if item_formatted is not None else str(item)))
                if formatted_items:
                    return "<br>".join(formatted_items), False
        except Exception:
            pass

    if field_type in (11, 13, 14) and isinstance(value, str) and "<" in value:
        return value, True

    formatted = _format_code_title_value(value)
    if formatted is not None:
        return escape(formatted), False

    return escape(_format_date_value(value)).replace("\n", "<br>"), False


def _parse_json_list(value):
    if isinstance(value, list):
        return value
    if not value:
        return None
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except Exception:
        return None
    return parsed if isinstance(parsed, list) else None


def _render_laboratory_results_table(value):
    rows_data = _parse_json_list(value)
    if not rows_data:
        return None

    header = (
        "<tr>"
        f'<th style="{_CELL_STYLE}"><strong>Анализ</strong></th>'
        f'<th style="{_CELL_STYLE}"><strong>Тест</strong></th>'
        f'<th style="{_CELL_STYLE}"><strong>Значение</strong></th>'
        f'<th style="{_CELL_STYLE}"><strong>Ед.изм</strong></th>'
        f'<th style="{_CELL_STYLE}"><strong>Дата</strong></th>'
        f'<th style="{_CELL_STYLE}"><strong>Исполнитель</strong></th>'
        "</tr>"
    )
    body_rows = []
    for row in rows_data:
        if not isinstance(row, dict):
            continue
        body_rows.append(
            "<tr>"
            f'<td style="{_CELL_STYLE}">{escape(str(row.get("researchTitle", "")))}</td>'
            f'<td style="{_CELL_STYLE}">{escape(str(row.get("fractionTitle", "")))}</td>'
            f'<td style="{_CELL_STYLE}">{escape(str(row.get("value", "")))}</td>'
            f'<td style="{_CELL_STYLE}">{escape(str(row.get("units", "")))}</td>'
            f'<td style="{_CELL_STYLE}">{escape(_format_date_value(row.get("date", "")))}</td>'
            f'<td style="{_CELL_STYLE}">{escape(str(row.get("docConfirm", "")))}</td>'
            "</tr>"
        )

    if not body_rows:
        return None
    return f'<table style="{_TABLE_STYLE}"><thead>{header}</thead><tbody>{"".join(body_rows)}</tbody></table>'


def _render_doc_referral_results_table(value):
    rows_data = _parse_json_list(value)
    if not rows_data:
        return None

    header = (
        "<tr>"
        f'<th style="{_CELL_STYLE}"><strong>Исследование</strong></th>'
        f'<th style="{_CELL_STYLE}"><strong>Дата</strong></th>'
        f'<th style="{_CELL_STYLE}"><strong>Врач</strong></th>'
        f'<th style="{_CELL_STYLE}"><strong>Результат</strong></th>'
        "</tr>"
    )
    body_rows = []
    for row in rows_data:
        if not isinstance(row, dict):
            continue
        result_value = escape(str(row.get("value", ""))).replace("\n", "<br>")
        body_rows.append(
            "<tr>"
            f'<td style="{_CELL_STYLE}">{escape(str(row.get("researchTitle", "")))}</td>'
            f'<td style="{_CELL_STYLE}">{escape(_format_date_value(row.get("date", "")))}</td>'
            f'<td style="{_CELL_STYLE}">{escape(str(row.get("docConfirm", "")))}</td>'
            f'<td style="{_CELL_STYLE}">{result_value}</td>'
            "</tr>"
        )

    if not body_rows:
        return None
    return f'<table style="{_TABLE_STYLE}"><thead>{header}</thead><tbody>{"".join(body_rows)}</tbody></table>'


def _render_procedure_list_table(value):
    rows_data = _parse_json_list(value)
    if not rows_data:
        return None

    body_rows = []
    for row in rows_data:
        if not isinstance(row, dict):
            continue
        pharma_title = row.get("pharmaTitle", "")
        mode = row.get("mode", "")
        if not pharma_title and not mode:
            continue
        body_rows.append(
            "<tr>"
            f'<td style="{_CELL_STYLE}">{escape(_format_date_value(pharma_title))}</td>'
            f'<td style="{_CELL_STYLE}">{escape(_format_date_value(mode))}</td>'
            "</tr>"
        )

    if not body_rows:
        return None
    return f'<table style="{_TABLE_STYLE}"><tbody>{"".join(body_rows)}</tbody></table>'


def _render_microbiology_section(microbiology):
    if not microbiology:
        return ""

    parts = []
    conclusion = microbiology.get("conclusion")
    if conclusion:
        parts.append(f"<p><strong>Заключение:</strong> {escape(conclusion)}</p>")

    for bactery in microbiology.get("bacteries", []):
        title = bactery.get("bacteryTitle") or bactery.get("bacteryGroupTitle") or "Микроорганизм"
        content_parts = []
        if bactery.get("koe"):
            content_parts.append(f"КОЕ: {escape(str(bactery['koe']))}")
        if bactery.get("comments"):
            content_parts.append(escape(bactery["comments"]))
        if content_parts:
            parts.append(f'<p><strong>{escape(title)}:</strong> {"<br>".join(content_parts)}</p>')
        else:
            parts.append(f"<p><strong>{escape(title)}:</strong></p>")

        antibiotics = bactery.get("antibiotics") or []
        if antibiotics:
            ab_rows = []
            for antibiotic in antibiotics:
                ab_rows.append(
                    "<tr>"
                    f'<td style="{_CELL_STYLE}">{escape(str(antibiotic.get("pk", "")))}</td>'
                    f'<td style="{_CELL_STYLE}">{escape(str(antibiotic.get("sri", "")))}</td>'
                    f'<td style="{_CELL_STYLE}">{escape(str(antibiotic.get("dia", "")))}</td>'
                    f'<td style="{_CELL_STYLE}">{escape(str(antibiotic.get("mic", "")))}</td>'
                    "</tr>"
                )
            parts.append(
                f'<table style="{_TABLE_STYLE}"><thead><tr>'
                f'<th style="{_CELL_STYLE}"><strong>Антибиотик</strong></th>'
                f'<th style="{_CELL_STYLE}"><strong>Чувствительность</strong></th>'
                f'<th style="{_CELL_STYLE}"><strong>DIA</strong></th>'
                f'<th style="{_CELL_STYLE}"><strong>MIC</strong></th>'
                f'</tr></thead><tbody>{"".join(ab_rows)}</tbody></table>'
            )

    return "".join(parts)


def _sort_by_order(items):
    return [
        item
        for _, item in sorted(
            enumerate(items or []),
            key=lambda pair: (pair[1].get("order", 0), pair[0], pair[1].get("pk", 0) or 0),
        )
    ]


def _render_field(field):
    display_value, allow_html = _format_field_display(field)
    if display_value in (None, ""):
        return ""

    field_title = field.get("title") or ""
    if field_title:
        return f"<p><strong>{escape(field_title)}:</strong> {display_value}</p>"
    return f"<p>{display_value}</p>"


def _collect_research_items(iss):
    research = iss.get("research") or {}
    items = [(research.get("title", ""), f"<p><strong>{escape(research.get('title', 'Исследование'))}:</strong></p>")]

    for group in research.get("groups") or []:
        group_title = group.get("title") or ""
        group_header = f"<p><strong>{escape(group_title)}:</strong></p>" if group.get("show_title") and group_title else ""

        for field in _sort_by_order(group.get("fields")):
            field_html = _render_field(field)
            if not field_html:
                continue
            if group_header:
                items.append((group_title, group_header))
                group_header = ""
            items.append((field.get("title") or "", field_html))

    microbiology_html = _render_microbiology_section(iss.get("microbiology"))
    if microbiology_html:
        items.append(("Микробиология", "<p><strong>Микробиология:</strong></p>" + microbiology_html))

    return items


def _render_research_section(iss, started=False):
    items = _collect_research_items(iss)
    if started:
        return "".join(html for _, html in items), True

    for index, (title, _) in enumerate(items):
        if _is_epicrisis_start(title):
            return "".join(html for _, html in items[index:]), True

    return "", False


def _extract_patient_birthday(patient):
    fio_age = (patient.get("fio_age") or "").strip()
    if not fio_age:
        return ""
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", fio_age)
    return match.group(1) if match else ""


def _render_service_fields_html(form_data):
    patient = form_data.get("patient") or {}
    direction = form_data.get("direction") or {}

    parts = []
    fio = (patient.get("fio") or "").strip()
    if fio:
        parts.append(f"<p><strong>ФИО:</strong> {escape(fio)}</p>")

    birthday = _extract_patient_birthday(patient)
    if birthday:
        parts.append(f"<p><strong>Дата рождения:</strong> {escape(birthday)}</p>")

    direction_pk = direction.get("pk")
    if direction_pk not in (None, ""):
        parts.append(f"<p><strong>Номер направления:</strong> {escape(str(direction_pk))}</p>")

    return "".join(parts)


def build_paraclinic_protocol_html(form_data):
    researches_html_parts = []
    started = False
    for iss in form_data.get("researches") or []:
        section_html, started = _render_research_section(iss, started=started)
        if section_html:
            researches_html_parts.append(section_html)

    researches_html = "".join(researches_html_parts)
    if not researches_html:
        return None, "Нет данных исследований для формирования HTML"

    service_fields_html = _render_service_fields_html(form_data)
    return f"{service_fields_html}{researches_html}", None
