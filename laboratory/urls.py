from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView, TemplateView

from users.views import home
from clients.views import ajax_search, receive_db, get_db
from researches.views import researches_get_one, get_all_tubes, tubes_control, tubes_relation
from directions.views import dir_save, gen_pdf_dir, get_one_dir, update_direction, cancel_direction, load_history, \
    print_history, \
    get_issledovaniya, get_client_directions, get_xls_dir, setdef, gen_pdf_execlist, get_worklist, group_confirm_get, \
    order_researches, resend
from receivematerial.views import receive, tubes_get, receive_obo, receive_history, receive_execlist, last_received, \
    receive_journal
from results.views import enter, loadready, results_save, result_get, result_conformation, result_confirm, result_print, \
    result_filter, get_full_result, get_odf_result, result_confirm_list, result_journal_print, get_day_results, \
    results_search, results_search_directions, result_html, result_journal_table_print
from construct import urls
from directory.views import directory_researches, directory_research, directory_researches_group, \
    directory_get_directions, directory_researches_list, directory_researches_update_uet, \
    directory_researches_update_mode, directory_toggle_hide_research, directory_copy_research, \
    directory_researches_update_sort, researches_update_template
from statistic.views import statistic_page, statistic_xls
import api.urls as api_urls
import barcodes.urls as barcodes_urls
from ajax_select import urls as ajax_select_urls
from django.contrib.auth.views import logout


admin.site.site_header = 'Администрирование L2'

urlpatterns = [
                  path('favicon\.ico', RedirectView.as_view(url='/static/icon/favicon.ico', permanent=True)),
                  path('', home, name='home'),
                  path('clients/ajax/search', ajax_search),
                  path('clients/import', receive_db),
                  path('clients/get_db', get_db),
                  path('directions/ajax/save', dir_save),
                  path('directions/resend', resend),
                  path('directions/pdf', gen_pdf_dir),
                  path('directions/execlist', gen_pdf_execlist),
                  path('directions/xls', get_xls_dir),
                  path('directions/def', setdef),
                  path('directions/get/one', get_one_dir),
                  path('directions/get/issledovaniya', get_issledovaniya),
                  path('directions/list/client', get_client_directions),
                  path('directions/worklist', get_worklist),
                  path('directions/order_researches', order_researches),
                  path('directions/group_confirm_get', group_confirm_get),
                  path('direction/researches/update', update_direction),
                  path('direction/researches/cancel', cancel_direction),
                  path('direction/researches/update/history', load_history),
                  path('direction/researches/update/history/print', print_history),
                  path('directory/tubes/all', get_all_tubes),
                  path('directory/tubes', tubes_control),
                  path('directory/tubes/relation', tubes_relation),
                  path('directory/research', directory_research),
                  path('directory/researches', directory_researches),
                  path('directory/researches/sort', directory_researches_update_sort),
                  path('directory/researches/hide/toggle', directory_toggle_hide_research),
                  path('directory/researches/copy', directory_copy_research),
                  path('directory/researches/group', directory_researches_group),
                  path('directory/researches/directions', directory_get_directions),
                  path('directory/researches/list', directory_researches_list),
                  path('directory/researches/update_uet', directory_researches_update_uet),
                  path('directory/researches/update_mode', directory_researches_update_mode),
                  path('directory/researches/update_template', researches_update_template),
                  path('researches/get/one', researches_get_one),
                  path('dashboard/', RedirectView.as_view(url='/mainmenu/')),
                  path('dashboard/', include('mainmenu.urls')),
                  path('mainmenu/', include('mainmenu.urls')),
                  path('mainmenu/receive', receive),
                  path('mainmenu/receive/one_by_one', receive_obo),
                  path('mainmenu/receive/last_received', last_received),
                  path('mainmenu/receive/execlist', receive_execlist),
                  path('mainmenu/receive/history', receive_history),
                  path('mainmenu/receive/journal', receive_journal),
                  path('tubes/get', tubes_get),
                  path('results/search', results_search),
                  path('results/search/directions', results_search_directions),
                  path('results/enter', enter),
                  path('results/save', results_save),
                  path('results/loadready', loadready),
                  path('results/get', result_get),
                  path('results/get/full', get_full_result),
                  path('results/get/odf', get_odf_result),
                  path('results/conformation', result_conformation),
                  path('results/confirm', result_confirm),
                  path('results/confirm/list', result_confirm_list),
                  path('results/pdf', result_print),
                  path('results/preview', TemplateView.as_view(template_name='dashboard/results_preview.html')),
                  path('results/html', result_html),
                  path('results/journal', result_journal_print),
                  path('results/journal_table', result_journal_table_print),
                  path('results/filter', result_filter),
                  path('results/day', get_day_results),
                  path('statistic', statistic_page),
                  path('statistic/xls', statistic_xls),
                  path('ajax_select/', include(ajax_select_urls)),
                  path('admin/doc/', include('django.contrib.admindocs.urls')),
                  path('admin/', admin.site.urls),
                  path('construct/', include(urls.urlpatterns)),
                  path('api/', include(api_urls.urlpatterns)),
                  path('barcodes/', include(barcodes_urls.urlpatterns)),
                  path('health/', include('health.urls')),
                  path('logout/', logout, {'next_page': '/'}),
                  path('o/', include('oauth2_provider.urls', namespace='oauth2_provider'))
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if 'silk' in settings.INSTALLED_APPS:
    urlpatterns.append(path('silk/', include('silk.urls', namespace='silk')))


if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(path('^__debug__/', include(debug_toolbar.urls)))
