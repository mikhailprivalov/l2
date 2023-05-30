from integration_framework.common_func import direction_pdf_content


def form_01(request_data):
    direction_id = int(request_data.get("direction"))
    if direction_id:
        return direction_pdf_content(direction_id)
