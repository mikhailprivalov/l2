from django.contrib import admin
from .models import WindowL2, ResourceL2, VoiceDo, StatusQueueL2
# Register your models here.

class ResResourceL2(admin.ModelAdmin):
    list_filter = ('windows_obj__title',)
    list_display = ('title', 'pk', 'windows_obj', 'letter','max_number', 'disable',)


class ResStatusQueueL2(admin.ModelAdmin):
    list_filter = ('queue_l2',)
    list_display = ('queue_l2', 'talon_letter', 'talon_number', 'status', 'date_get', 'date_invite', 'doc_invite',)


admin.site.register(WindowL2)
admin.site.register(ResourceL2, ResResourceL2)
admin.site.register(VoiceDo)
admin.site.register(StatusQueueL2, ResStatusQueueL2)
