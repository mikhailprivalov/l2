from ajax_select import register, LookupChannel
import directory.models as dir_models


@register('fraction')
class FractionLookup(LookupChannel):

    model = dir_models.Fractions

    def get_query(self, q, request):
        return self.model.objects.filter(title__icontains=q, hide=False, research__hide=False).order_by('title')