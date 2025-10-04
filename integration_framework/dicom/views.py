from rest_framework.response import Response
from rest_framework.decorators import api_view
from integration_framework.models import EquipmentReceive


@api_view(['POST'])
def get_meta_tags(request):
    result = EquipmentReceive.save_meta_tag_from_dicom_server(request)

    return Response({"result": result})
