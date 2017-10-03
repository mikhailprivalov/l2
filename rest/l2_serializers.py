from django.contrib.auth.models import User
from rest_framework import serializers

from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.HyperlinkedRelatedField(
        many=False,
        view_name='doctorprofiles'
    )
    class Meta:
        model = User
        fields = ('username', 'is_staff', 'profile')


class DoctorSerializer(serializers.ModelSerializer):
    podrazileniye = serializers.HyperlinkedRelatedField(
        many=False,
        view_name='podrazdeleniyas'
    )
    class Meta:
        model = DoctorProfile
        fields = ('user', 'fio', 'podrazileniye', 'isLDAP_user', 'labtype')


class PodrazdeleniyaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Podrazdeleniya
        fields = ('title', 'gid_n', 'isLab', 'hide')
