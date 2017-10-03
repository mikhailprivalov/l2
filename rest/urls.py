from django.conf.urls import url, include
from rest_framework import routers

from rest.l2_view_sets import UserViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'doctorprofiles', DoctorSerializer)
router.register(r'podrazdeleniyas', PodrazdeleniyaSerializer)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
