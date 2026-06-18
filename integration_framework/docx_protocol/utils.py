import ast
import re

import simplejson as json
from django.http import HttpRequest
from django.utils.html import escape

from utils.dates import normalize_date

DISCHARGE_DATE_TITLES = ("в.э.-Дата выписки", "Дата выписки")

_FONT_SIZE = "11pt"
_TABLE_FONT_SIZE = "8pt"
_LAB_TABLE_FONT_SIZE = "6pt"
_P_ATTR = f'style="font-size:{_FONT_SIZE};line-height:1.3;margin:0 0 4px 0"'


def _p(content):
    return f"<p {_P_ATTR}>{content}</p>"


_TABLE_MAX_WIDTH_MM = 165
_TABLE_MAX_WIDTH = f"{_TABLE_MAX_WIDTH_MM}mm"
_LAB_VALUE_COL_MM = 7.5
_LAB_NARROW_COL_MM = 8
_LAB_TABLE_MAX_WIDTH_MM = 180
_LAB_TABLE_MAX_WIDTH = f"{_LAB_TABLE_MAX_WIDTH_MM}mm"

_TABLE_BORDER_COLOR = "#000000"
_TABLE_BORDER = f"1pt solid {_TABLE_BORDER_COLOR}"

_TABLE_OPEN = (
    f'<table border="1" bordercolor="{_TABLE_BORDER_COLOR}" cellspacing="0" cellpadding="2" '
    f'width="{_TABLE_MAX_WIDTH_MM}mm" '
    f'style="width:{_TABLE_MAX_WIDTH};max-width:{_TABLE_MAX_WIDTH};'
    f'border-collapse:collapse;border:{_TABLE_BORDER};table-layout:fixed;word-wrap:break-word">'
)
_TABLE_CLOSE = "</table>"
_CELL_STYLE = (
    f"border:{_TABLE_BORDER};border-color:{_TABLE_BORDER_COLOR};"
    "padding:2px 4px;vertical-align:top;"
    f"word-wrap:break-word;overflow-wrap:break-word;font-size:{_TABLE_FONT_SIZE}"
)
_LAB_CELL_STYLE = (
    f"border:{_TABLE_BORDER};border-color:{_TABLE_BORDER_COLOR};"
    "padding:0;vertical-align:middle;text-align:center;"
    f"word-wrap:break-word;overflow-wrap:break-word;word-break:break-word;"
    f"font-size:{_LAB_TABLE_FONT_SIZE};line-height:1.05"
)
_CELL_BORDER_ATTR = 'border="1"'
_AGG_KEY_DELIMITER = "#@#"
_AGGREGATE_FIELD_HTML_TAGS = ("sub", "sup", "u", "p", "strong", "em")


def _lab_table_open(table_width_mm):
    table_width_mm = min(round(table_width_mm, 2), _LAB_TABLE_MAX_WIDTH_MM)
    table_width = f"{table_width_mm}mm"
    return (
        f'<table border="1" bordercolor="{_TABLE_BORDER_COLOR}" cellspacing="0" cellpadding="0" '
        f'width="{table_width_mm}mm" '
        f'style="width:{table_width};max-width:{_LAB_TABLE_MAX_WIDTH};'
        f'border-collapse:collapse;border:{_TABLE_BORDER};table-layout:fixed;word-wrap:break-word">'
    )


def _lab_col_width_mm(num_columns):
    if num_columns <= 0:
        return _LAB_VALUE_COL_MM
    natural_width = _LAB_VALUE_COL_MM * num_columns
    if natural_width <= _LAB_TABLE_MAX_WIDTH_MM:
        return _LAB_VALUE_COL_MM
    return round(_LAB_TABLE_MAX_WIDTH_MM / num_columns, 2)


def _lab_colgroup_vertical(num_fractions):
    if num_fractions <= 0:
        return ""
    num_columns = 1 + num_fractions
    col_width = _lab_col_width_mm(num_columns)
    cols = [f'<col width="{col_width}mm" style="width:{col_width}mm">']
    cols.extend(f'<col width="{col_width}mm" style="width:{col_width}mm">' for _ in range(num_fractions))
    return f"<colgroup>{''.join(cols)}</colgroup>"


def _lab_colgroup_horizontal(num_dates):
    if num_dates <= 0:
        return ""
    num_columns = 1 + num_dates
    col_width = _lab_col_width_mm(num_columns)
    cols = [f'<col width="{col_width}mm" style="width:{col_width}mm">']
    cols.extend(f'<col width="{col_width}mm" style="width:{col_width}mm">' for _ in range(num_dates))
    return f"<colgroup>{''.join(cols)}</colgroup>"


def _lab_vertical_col_widths(num_fractions):
    num_columns = 1 + num_fractions
    col_width = _lab_col_width_mm(num_columns)
    return [col_width] * num_columns


def _lab_horizontal_col_widths(num_dates):
    num_columns = 1 + num_dates
    col_width = _lab_col_width_mm(num_columns)
    return [col_width] * num_columns


def _lab_table_width_mm(num_columns):
    return min(_LAB_VALUE_COL_MM * num_columns, _LAB_TABLE_MAX_WIDTH_MM)


def _lab_font_size(width_mm):
    if width_mm <= _LAB_VALUE_COL_MM:
        return "5.5pt"
    if width_mm < 7:
        return "5pt"
    if width_mm < _LAB_NARROW_COL_MM:
        return "5.5pt"
    return _LAB_TABLE_FONT_SIZE


def _lab_cell(tag, content, width_mm):
    font_size = _lab_font_size(width_mm)
    cell_style = _LAB_CELL_STYLE.replace(f"font-size:{_LAB_TABLE_FONT_SIZE}", f"font-size:{font_size}")
    return (
        f'<{tag} {_CELL_BORDER_ATTR} width="{width_mm}mm" '
        f'style="{cell_style};width:{width_mm}mm;max-width:{width_mm}mm;min-width:{width_mm}mm">'
        f'{content}</{tag}>'
    )


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

    header = "".join(f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(title))}</th>' for title in columns)
    body_rows = []
    for row in rows:
        if not isinstance(row, list):
            continue
        cells = "".join(f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{_display_text_value(cell)}</td>' for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")

    if not body_rows:
        return ""

    return f'{_TABLE_OPEN}<thead><tr>{header}</tr></thead><tbody>{"".join(body_rows)}</tbody>{_TABLE_CLOSE}'


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

    if field_type == 16:
        table = _render_aggregate_laboratory_table(value)
        if table:
            return table, True

    if field_type == 17:
        content = _render_aggregate_desc_html(value)
        if content:
            return content, True

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


def _parse_directions_field_value(value):
    if value in (None, ""):
        return None
    try:
        data = json.loads(value) if isinstance(value, str) else value
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    directions = data.get("directions") or []
    if not directions:
        return None
    excluded = data.get("excluded")
    if excluded is None:
        excluded = []
    return {"directions": directions, "excluded": excluded}


def _normalize_lab_excluded(excluded):
    if isinstance(excluded, dict):
        return {
            "dateDir": excluded.get("dateDir") or [],
            "titles": excluded.get("titles") or [],
        }
    return {"dateDir": [], "titles": []}


def _filter_directions_by_excluded(directions, excluded):
    if not isinstance(excluded, list):
        return directions
    excluded_ids = [item for item in excluded if isinstance(item, int)]
    if not excluded_ids:
        return directions
    return [direction for direction in directions if direction not in excluded_ids]


def _get_excluded_date_dir_keys(excluded):
    keys = []
    if isinstance(excluded, dict):
        keys.extend(excluded.get("dateDir") or [])
    elif isinstance(excluded, list):
        keys.extend(item for item in excluded if isinstance(item, str) and _AGG_KEY_DELIMITER in item)
    return keys


def _is_aggregate_date_excluded(date, group, excluded_keys):
    if not excluded_keys:
        return False
    return f"{group}{_AGG_KEY_DELIMITER}{date}" in excluded_keys


def _sanitize_aggregate_field_html(value):
    text = str(value or "")
    text = escape(text)
    for tag in _AGGREGATE_FIELD_HTML_TAGS:
        text = text.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        text = text.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    return text.replace("\n", "<br>")


def _render_aggregate_laboratory_table(value):
    parsed = _parse_directions_field_value(value)
    if not parsed:
        return None

    from api.stationar.stationar_func import hosp_get_lab_iss

    excluded = _normalize_lab_excluded(parsed["excluded"])
    exclude_direction = excluded["dateDir"]
    exclude_fraction = excluded["titles"]
    exclude_direction_final = [item.split(_AGG_KEY_DELIMITER)[1] for item in exclude_direction if _AGG_KEY_DELIMITER in item]

    lab_iss = hosp_get_lab_iss(None, False, parsed["directions"])
    if not lab_iss:
        return None

    parts = []
    for type_lab, lab_data in lab_iss.items():
        vertical_blocks = lab_data.get("vertical") or []
        for block in vertical_blocks:
            title_research = block.get("title_research", "")
            title_fractions = block.get("title_fracions") or []
            fractions_result = block.get("result") or {}

            fractions_index_to_remove = []
            for index, fraction in enumerate(title_fractions):
                maybe_exclude_fraction = f"{title_research}{_AGG_KEY_DELIMITER}{fraction}"
                if maybe_exclude_fraction in exclude_fraction:
                    fractions_index_to_remove.append(index)

            visible_fractions = [fraction for index, fraction in enumerate(title_fractions) if index not in fractions_index_to_remove]
            if not visible_fractions:
                continue

            col_widths = _lab_vertical_col_widths(len(visible_fractions))
            header_cells = [_lab_cell("th", "Дата", col_widths[0])]
            header_cells.extend(_lab_cell("th", escape(fraction), col_widths[index + 1]) for index, fraction in enumerate(visible_fractions))
            body_rows = []
            for date_dir, values in fractions_result.items():
                if date_dir in exclude_direction_final:
                    continue
                row_cells = [_lab_cell("td", escape(date_dir), col_widths[0])]
                has_value = False
                value_col_index = 1
                for index, cell_value in enumerate(values):
                    if index in fractions_index_to_remove:
                        continue
                    cell_text = str(cell_value or "")
                    if cell_text.strip():
                        has_value = True
                    row_cells.append(_lab_cell("td", escape(cell_text), col_widths[value_col_index]))
                    value_col_index += 1
                if has_value:
                    body_rows.append(f"<tr>{''.join(row_cells)}</tr>")

            if not body_rows:
                continue

            colspan = len(visible_fractions) + 1
            table_width_mm = _lab_table_width_mm(colspan)
            table_width = f"{table_width_mm}mm"
            parts.append(
                f'{_lab_table_open(table_width_mm)}'
                f'{_lab_colgroup_vertical(len(visible_fractions))}'
                f'<thead>'
                f'<tr><th {_CELL_BORDER_ATTR} colspan="{colspan}" '
                f'width="{table_width_mm}mm" '
                f'style="{_LAB_CELL_STYLE};width:{table_width};max-width:{_LAB_TABLE_MAX_WIDTH};'
                f'font-size:5.5pt;word-break:break-word">'
                f'<strong>{escape(title_research)}</strong></th></tr>'
                f'<tr>{"".join(header_cells)}</tr>'
                f'</thead>'
                f'<tbody>{"".join(body_rows)}</tbody>'
                f'{_TABLE_CLOSE}'
            )

        horizontal_blocks = lab_data.get("horizontal") or []
        for block in horizontal_blocks:
            title_fractions = block.get("title_fracions") or []
            fractions_result = block.get("result") or {}

            fractions_index_to_remove = []
            for index, fraction in enumerate(title_fractions):
                maybe_exclude_fraction = f"{type_lab}{_AGG_KEY_DELIMITER}{fraction}"
                if maybe_exclude_fraction in exclude_fraction:
                    fractions_index_to_remove.append(index)

            visible_fractions = [fraction for index, fraction in enumerate(title_fractions) if index not in fractions_index_to_remove]
            visible_dates = list(fractions_result.keys())
            if not visible_fractions or not visible_dates:
                continue

            col_widths = _lab_horizontal_col_widths(len(visible_dates))
            header_cells = [_lab_cell("th", "Анализ", col_widths[0])]
            header_cells.extend(_lab_cell("th", escape(date_dir), col_widths[index + 1]) for index, date_dir in enumerate(visible_dates))
            body_rows = []
            for fraction in title_fractions:
                if fraction not in visible_fractions:
                    continue
                index_result = title_fractions.index(fraction)
                row_cells = [_lab_cell("th", escape(fraction), col_widths[0])]
                for col_index, values in enumerate(fractions_result.values()):
                    cell_text = str(values[index_result] if index_result < len(values) else "")
                    row_cells.append(_lab_cell("td", escape(cell_text), col_widths[col_index + 1]))
                body_rows.append(f"<tr>{''.join(row_cells)}</tr>")

            if not body_rows:
                continue

            colspan = len(visible_dates) + 1
            table_width_mm = _lab_table_width_mm(colspan)
            table_width = f"{table_width_mm}mm"
            parts.append(
                f'{_lab_table_open(table_width_mm)}'
                f'{_lab_colgroup_horizontal(len(visible_dates))}'
                f'<thead>'
                f'<tr><th {_CELL_BORDER_ATTR} colspan="{colspan}" '
                f'width="{table_width_mm}mm" '
                f'style="{_LAB_CELL_STYLE};width:{table_width};max-width:{_LAB_TABLE_MAX_WIDTH};'
                f'font-size:5.5pt;word-break:break-word">'
                f'<strong>{escape(type_lab)}</strong></th></tr>'
                f'<tr>{"".join(header_cells)}</tr>'
                f'</thead>'
                f'<tbody>{"".join(body_rows)}</tbody>'
                f'{_TABLE_CLOSE}'
            )

    if not parts:
        return None
    return "".join(parts)


def _render_aggregate_desc_html(value):
    parsed = _parse_directions_field_value(value)
    if not parsed:
        return None

    from api.stationar.stationar_func import hosp_get_text

    directions = _filter_directions_by_excluded(parsed["directions"], parsed["excluded"])
    if not directions:
        return None

    excluded_keys = _get_excluded_date_dir_keys(parsed["excluded"])
    text_iss = hosp_get_text(None, False, None, directions)
    if not text_iss:
        return None

    parts = []
    for research in text_iss:
        title_research = research.get("title_research", "")
        research_parts = []
        for result in research.get("result") or []:
            date = result.get("date", "")
            if not date or _is_aggregate_date_excluded(date, title_research, excluded_keys):
                continue

            date_parts = []

            for group in result.get("data") or []:
                group_title = (group.get("group_title") or "").strip()
                fields_html = []
                for field in group.get("fields") or []:
                    field_value = field.get("value", "")
                    if field_value in (None, ""):
                        continue
                    title_field = (field.get("title_field") or "").strip()
                    value_html = _sanitize_aggregate_field_html(field_value)
                    if title_field:
                        fields_html.append(f"<strong>{escape(title_field)}:</strong> {value_html}")
                    else:
                        fields_html.append(value_html)

                if not fields_html and not group_title:
                    continue

                group_html = " ".join(fields_html)
                if group_title:
                    date_parts.append(f"<strong>{escape(group_title)}:</strong> {group_html}")
                else:
                    date_parts.append(group_html)

            if date_parts:
                research_parts.append(_p(f'<strong>{escape(date)}:</strong> {" ".join(date_parts)}'))

        if research_parts:
            if title_research:
                parts.append(_p(f"<strong>{escape(title_research)}</strong>"))
            parts.extend(research_parts)

    if not parts:
        return None
    return "".join(parts)


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
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Анализ</strong></th>'
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Тест</strong></th>'
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Значение</strong></th>'
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Ед.изм</strong></th>'
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Дата</strong></th>'
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Исполнитель</strong></th>'
        "</tr>"
    )
    body_rows = []
    for row in rows_data:
        if not isinstance(row, dict):
            continue
        body_rows.append(
            "<tr>"
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(row.get("researchTitle", "")))}</td>'
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(row.get("fractionTitle", "")))}</td>'
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(row.get("value", "")))}</td>'
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(row.get("units", "")))}</td>'
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(_format_date_value(row.get("date", "")))}</td>'
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(row.get("docConfirm", "")))}</td>'
            "</tr>"
        )

    if not body_rows:
        return None
    return f'{_TABLE_OPEN}<thead>{header}</thead><tbody>{"".join(body_rows)}</tbody>{_TABLE_CLOSE}'


def _render_doc_referral_results_table(value):
    rows_data = _parse_json_list(value)
    if not rows_data:
        return None

    header = (
        "<tr>"
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Исследование</strong></th>'
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Дата</strong></th>'
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Врач</strong></th>'
        f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Результат</strong></th>'
        "</tr>"
    )
    body_rows = []
    for row in rows_data:
        if not isinstance(row, dict):
            continue
        result_value = escape(str(row.get("value", ""))).replace("\n", "<br>")
        body_rows.append(
            "<tr>"
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(row.get("researchTitle", "")))}</td>'
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(_format_date_value(row.get("date", "")))}</td>'
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(row.get("docConfirm", "")))}</td>'
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{result_value}</td>'
            "</tr>"
        )

    if not body_rows:
        return None
    return f'{_TABLE_OPEN}<thead>{header}</thead><tbody>{"".join(body_rows)}</tbody>{_TABLE_CLOSE}'


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
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(_format_date_value(pharma_title))}</td>'
            f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(_format_date_value(mode))}</td>'
            "</tr>"
        )

    if not body_rows:
        return None
    return f'{_TABLE_OPEN}<tbody>{"".join(body_rows)}</tbody>{_TABLE_CLOSE}'


def _render_microbiology_section(microbiology):
    if not microbiology:
        return ""

    parts = []
    conclusion = microbiology.get("conclusion")
    if conclusion:
        parts.append(_p(f"<strong>Заключение:</strong> {escape(conclusion)}"))

    for bactery in microbiology.get("bacteries", []):
        title = bactery.get("bacteryTitle") or bactery.get("bacteryGroupTitle") or "Микроорганизм"
        content_parts = []
        if bactery.get("koe"):
            content_parts.append(f"КОЕ: {escape(str(bactery['koe']))}")
        if bactery.get("comments"):
            content_parts.append(escape(bactery["comments"]))
        if content_parts:
            parts.append(_p(f'<strong>{escape(title)}:</strong> {"<br>".join(content_parts)}'))
        else:
            parts.append(_p(f"<strong>{escape(title)}:</strong>"))

        antibiotics = bactery.get("antibiotics") or []
        if antibiotics:
            ab_rows = []
            for antibiotic in antibiotics:
                ab_rows.append(
                    "<tr>"
                    f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(antibiotic.get("pk", "")))}</td>'
                    f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(antibiotic.get("sri", "")))}</td>'
                    f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(antibiotic.get("dia", "")))}</td>'
                    f'<td {_CELL_BORDER_ATTR} style="{_CELL_STYLE}">{escape(str(antibiotic.get("mic", "")))}</td>'
                    "</tr>"
                )
            parts.append(
                f'{_TABLE_OPEN}<thead><tr>'
                f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Антибиотик</strong></th>'
                f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>Чувствительность</strong></th>'
                f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>DIA</strong></th>'
                f'<th {_CELL_BORDER_ATTR} style="{_CELL_STYLE}"><strong>MIC</strong></th>'
                f'</tr></thead><tbody>{"".join(ab_rows)}</tbody>{_TABLE_CLOSE}'
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
        return _p(f"<strong>{escape(field_title)}:</strong> {display_value}")
    return _p(display_value)


def _collect_research_items(iss):
    research = iss.get("research") or {}
    items = []

    for group in research.get("groups") or []:
        group_title = group.get("title") or ""
        group_header = _p(f"<strong>{escape(group_title)}:</strong>") if group.get("show_title") and group_title else ""

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
        items.append(("Микробиология", _p("<strong>Микробиология:</strong>") + microbiology_html))

    if not items:
        return []

    research_title = research.get("title", "Исследование")
    items.insert(0, (research_title, _p(f"<strong>{escape(research_title)}:</strong>")))
    return items


def _render_research_section(iss):
    items = _collect_research_items(iss)
    return "".join(html for _, html in items)


def _extract_patient_birthday(patient):
    fio_age = (patient.get("fio_age") or "").strip()
    if not fio_age:
        return ""
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", fio_age)
    return match.group(1) if match else ""


def _format_person_date(value):
    if value in (None, ""):
        return ""

    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return normalize_date(text[:10])
    return normalize_date(text)


def _find_field_value_by_title(form_data, title):
    for iss in form_data.get("researches") or []:
        research = iss.get("research") or {}
        for group in research.get("groups") or []:
            for field in group.get("fields") or []:
                if (field.get("title") or "").strip() == title:
                    value = field.get("value")
                    if value not in (None, ""):
                        return value
    return ""


def _find_discharge_date_in_form_data(form_data):
    for title in DISCHARGE_DATE_TITLES:
        value = _find_field_value_by_title(form_data, title)
        if value not in (None, ""):
            formatted = _format_person_date(value)
            if formatted:
                return formatted
    return ""


def build_patient_data(form_data):
    patient = form_data.get("patient") or {}
    return {
        "fullFio": (patient.get("fio") or "").strip(),
        "birthday": _extract_patient_birthday(patient),
        "dateExtract": _find_discharge_date_in_form_data(form_data),
    }


def _render_service_fields_html(form_data):
    patient = form_data.get("patient") or {}
    direction = form_data.get("direction") or {}

    parts = []
    fio = (patient.get("fio") or "").strip()
    if fio:
        parts.append(_p(f"<strong>ФИО:</strong> {escape(fio)}"))

    birthday = _extract_patient_birthday(patient)
    if birthday:
        parts.append(_p(f"<strong>Дата рождения:</strong> {escape(birthday)}"))

    direction_pk = direction.get("pk")
    if direction_pk not in (None, ""):
        parts.append(_p(f"<strong>Номер направления:</strong> {escape(str(direction_pk))}"))

    return "".join(parts)


def build_paraclinic_protocol_html(form_data):
    researches_html_parts = []
    for iss in form_data.get("researches") or []:
        section_html = _render_research_section(iss)
        if section_html:
            researches_html_parts.append(section_html)

    researches_html = "".join(researches_html_parts)
    if not researches_html:
        return None, "Нет данных исследований для формирования HTML"

    service_fields_html = _render_service_fields_html(form_data)
    return f"{service_fields_html}{researches_html}", None
