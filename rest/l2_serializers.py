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
#         fields = ('url', 'user', 'fio', 'podrazdeleniye', 'isLDAP_user', 'labtype')
#
#
# class PodrazdeleniyaSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Podrazdeleniya
#         fields = ('url', 'title', 'gid_n', 'isLab', 'hide')
