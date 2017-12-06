from django.urls import path, include
from rest_framework import routers

# from rest.l2_serializers import DoctorSerializer, PodrazdeleniyaSerializer
# from rest.l2_view_sets import UserViewSet

router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)
# router.register(r'doctorprofiles', DoctorSerializer)
# router.register(r'podrazdeleniyas', PodrazdeleniyaSerializer)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
