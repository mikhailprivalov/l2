from ajax_select import urls as ajax_select_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import RedirectView

import clients.views
import directions.views
import mainmenu.views
import receivematerial.views
import researches.views
import statistic.views
from users.views import home

admin.site.site_header = 'Администрирование L2'

handler404 = mainmenu.views.v404

if not settings.DEBUG:
    handler500 = mainmenu.views.v500


def trigger_error(request):
    return 1 / 0


urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/icon/favicon.ico', permanent=True)),
    path('', home, name='home'),
    path('clients/import', clients.views.receive_db),
    path('clients/get_db', clients.views.get_db),
    path('clients/search_phone', clients.views.search_phone),
    path('directions/', include('directions.urls')),
    path('direction/researches/update', directions.views.update_direction),
    path('direction/researches/cancel', directions.views.cancel_direction),
    path('direction/researches/update/history', directions.views.load_history),
    path('direction/researches/update/history/print', directions.views.print_history),
    path('directory/', include('directory.urls')),
    path('researches/get/one', researches.views.researches_get_one),
    path('dashboard/', include('mainmenu.urls')),
    path('mainmenu/', include('mainmenu.urls')),
    path('forms/', include('forms.urls')),
    path('cases/', include('cases.urls')),
    path('tubes/get', receivematerial.views.tubes_get),
    path('results/', include('results.urls')),
    path('laboratory/', include('results.urls')),
    path('statistic', statistic.views.statistic_page),
    path('statistic/xls', statistic.views.statistic_xls),
    path('ajax_select/', include(ajax_select_urls)),
    path('admin/', admin.site.urls),
    path('construct/', include('construct.urls')),
    path('api/', include('api.urls')),
    path('barcodes/', include('barcodes.urls')),
    path('health/', include('health.urls')),
    path('reports/', include('reports.urls')),
    path('mq/', include('mq.urls')),
    path('logout/', LogoutView.as_view(), {'next_page': '/'}),
    path('if/', include('integration_framework.urls')),
    path('medical_certificates/', include('medical_certificates.urls')),
    path('sentry-debug/', trigger_error),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if 'silk' in settings.INSTALLED_APPS:
    urlpatterns.append(path('silk/', include('silk.urls', namespace='silk')))

if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
