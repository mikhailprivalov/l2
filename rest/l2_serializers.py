from django.contrib.auth.models import User
from rest_framework import serializers

from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile

#
# class UserSerializer(serializers.HyperlinkedModelSerializer):
#     profile =
#     class Meta:
#         model = User
#         fields = ('url', 'username', 'email', 'is_staff', 'doctorprofile')
#
#
# class DoctorSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = DoctorProfile
#         fields = ('url', 'user', 'fio', 'podrazileniye', 'isLDAP_user', 'labtype')
#
#
# class PodrazdeleniyaSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Podrazdeleniya
#         fields = ('url', 'title', 'gid_n', 'isLab', 'hide')
