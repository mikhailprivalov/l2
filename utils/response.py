from typing import Optional
from django.http import JsonResponse


def status_response(ok: bool, message: Optional[str] = None, data: Optional[dict] = None):
    return JsonResponse({"ok": ok, "message": message, **(data or {})})
