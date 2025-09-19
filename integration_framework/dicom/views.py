from rest_framework.response import Response
from rest_framework.decorators import api_view
import simplejson as json
from integration_framework.models import EquipmentReceive


@api_view()
def get_meta_tags(request):
    data = json.loads(request.body)
    result = EquipmentReceive.save_meta_tag_from_dicom_server(data)

    return Response({"result": result})
