from ajax_select import urls as ajax_select_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path, re_path
from django.views.generic import RedirectView

import clients.views
import directions.views
import mainmenu.views
import receivematerial.views
import statistic.views
from users.views import home

admin.site.site_header = 'Администрирование L2'

handler404 = mainmenu.views.v404

if not settings.DEBUG:
    handler500 = mainmenu.views.v500


urlpatterns = ([] if not settings.PROMETHEUS_ENABLED else [path('prometheus/', include('django_prometheus.urls'))]) + [
    path('favicon.ico', RedirectView.as_view(url='/static/icon/favicon.ico', permanent=True)),
    path('', home, name='home'),
    re_path(r'^ui/(?P<path>.*)$', mainmenu.views.ui),
    path('clients/import', clients.views.receive_db),
    path('clients/get_db', clients.views.get_db),
    path('clients/search_phone', clients.views.search_phone),
    path('directions/', include('directions.urls')),
    path('direction/researches/update/history/print', directions.views.print_history),
    path('directory/', include('directory.urls')),
    path('dashboard/', include('mainmenu.urls')),
    path('mainmenu/', include('mainmenu.urls')),
    path('forms/', include('forms.urls')),
    path('cases/', include('cases.urls')),
    path('tubes/get', receivematerial.views.tubes_get),
    path('results/', include('results.urls')),
    path('laboratory/', include('results.urls')),
    path('statistic/xls', statistic.views.statistic_xls),
    path('statistic/screening', statistic.views.sreening_xls),
    path('statistic/open-xls', statistic.views.open_xls),
    path('statistic/harmful-factors', statistic.views.get_harmful_factors),
    path('ajax_select/', include(ajax_select_urls)),
    path('admin/login/', RedirectView.as_view(url='/')),
    path('admin/', admin.site.urls),
    path('construct/', include('construct.urls')),
    path('api/', include('api.urls')),
    path('barcodes/', include('barcodes.urls')),
    path('reports/', include('reports.urls')),
    path('logout/', mainmenu.views.logout_view),
    path('if/', include('integration_framework.urls')),
    path('medical_certificates/', include('medical_certificates.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
