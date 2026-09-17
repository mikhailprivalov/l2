import os
from io import BytesIO
from typing import Iterable, List, Optional, TYPE_CHECKING

from PIL import Image, ImageOps
from django.db.models import Prefetch
from pdfrw import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from directions.models import Issledovaniya, ParaclinicResult, ParaclinicResultFile
from directory.models import ParaclinicInputField

if TYPE_CHECKING:
    from hospitals.models import Hospitals

IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png"})
APPENDIX_MAX_WIDTH_MM = 170
APPENDIX_MAX_HEIGHT_MM = 240


def hospital_for_paraclinic_pdf_appendix(direction, iss: Issledovaniya) -> Optional["Hospitals"]:
    if direction.hospital_id:
        return direction.hospital
    if iss.doc_confirmation_id and iss.doc_confirmation.hospital_id:
        return iss.doc_confirmation.hospital
    return None


def should_append_paraclinic_file_images(hospital: Optional["Hospitals"]) -> bool:
    return bool(hospital and getattr(hospital, "append_paraclinic_file_images_to_result_pdf", False))


def _extension_allowed(extension: str, allowed_extensions: Iterable[str]) -> bool:
    ext = (extension or "").lower().lstrip(".")
    if ext not in IMAGE_EXTENSIONS:
        return False
    allowed = [a.lower().lstrip(".") for a in (allowed_extensions or []) if a]
    if not allowed:
        return True
    return ext in allowed


def get_paraclinic_image_files_for_pdf(iss: Issledovaniya) -> List[ParaclinicResultFile]:
    results = (
        ParaclinicResult.objects.filter(issledovaniye_id=iss.pk, field_type=42)
        .select_related("field", "field__group", "field__file_settings")
        .prefetch_related(Prefetch("files", queryset=ParaclinicResultFile.objects.order_by("created_at", "pk")))
        .order_by("field__group__order", "field__order", "pk")
    )

    collected: List[ParaclinicResultFile] = []
    for result in results:
        field: ParaclinicInputField = result.field
        if not field or field.hide:
            continue
        allowed = []
        if getattr(field, "file_settings", None):
            allowed = field.file_settings.allowed_extensions or []
        for file_row in result.files.all():
            if not _extension_allowed(file_row.extension, allowed):
                continue
            path = file_row.file.path if file_row.file else None
            if not path or not os.path.exists(path):
                continue
            collected.append(file_row)
    return collected


def _fit_image_size_pt(image_path: str):
    page_w, page_h = A4
    max_w = APPENDIX_MAX_WIDTH_MM * mm
    max_h = APPENDIX_MAX_HEIGHT_MM * mm
    with Image.open(image_path) as img:
        img = ImageOps.exif_transpose(img)
        width_px, height_px = img.size
    if not width_px or not height_px:
        return max_w, max_h
    width_pt = max_w
    height_pt = width_pt * height_px / width_px
    if height_pt > max_h:
        height_pt = max_h
        width_pt = height_pt * width_px / height_px
    return width_pt, height_pt


def _image_page_pdf_bytes(image_path: str) -> bytes:
    buf = BytesIO()
    page_w, page_h = A4
    width_pt, height_pt = _fit_image_size_pt(image_path)
    x = (page_w - width_pt) / 2
    y = (page_h - height_pt) / 2
    c = canvas.Canvas(buf, pagesize=A4)
    c.drawImage(image_path, x, y, width=width_pt, height=height_pt, preserveAspectRatio=True)
    c.showPage()
    c.save()
    return buf.getvalue()


def append_paraclinic_images_to_pdf(pdf_bytes: bytes, iss: Issledovaniya, hospital: Optional["Hospitals"]) -> bytes:
    if not should_append_paraclinic_file_images(hospital):
        return pdf_bytes
    image_files = get_paraclinic_image_files_for_pdf(iss)
    if not image_files:
        return pdf_bytes

    writer = PdfWriter()
    pdf_all = BytesIO()
    writer.addpages(PdfReader(BytesIO(pdf_bytes)).pages)
    for file_row in image_files:
        path = file_row.file.path
        if not path or not os.path.exists(path):
            continue
        writer.addpages(PdfReader(BytesIO(_image_page_pdf_bytes(path))).pages)
    writer.write(pdf_all)
    return pdf_all.getvalue()
