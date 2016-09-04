from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from users.views import home
from clients.views import ajax_search
from researches.views import ajax_search_res, researches_get_one, get_all_tubes, tubes_control, tubes_relation
from directions.views import dir_save, gen_pdf_dir, get_one_dir, update_direction, cancel_direction, load_history, \
    print_history, \
    get_issledovaniya, get_client_directions, get_xls_dir, setdef, gen_pdf_execlist, get_worklist, group_confirm_get
from receivematerial.views import receive, tubes_get, receive_obo, receive_history, receive_execlist, last_received, \
    receive_journal
from results.views import enter, loadready, results_save, result_get, result_conformation, result_confirm, result_print, \
    result_filter, get_full_result, get_odf_result, result_confirm_list, result_journal_print, get_day_results, \
    results_search, results_search_directions, result_html
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


urlpatterns = [
                  url(r'^$', home, name='home'),
                  url(r'^clients/ajax/search$', ajax_search),
                  url(r'^directions/ajax/save$', dir_save),
                  url(r'^directions/pdf$', gen_pdf_dir),
                  url(r'^directions/execlist', gen_pdf_execlist),
                  url(r'^directions/xls$', get_xls_dir),
                  url(r'^directions/def$', setdef),
                  url(r'^directions/get/one$', get_one_dir),
                  url(r'^directions/get/issledovaniya', get_issledovaniya),
                  url(r'^directions/list/client$', get_client_directions),
                  url(r'^directions/worklist$', get_worklist),
                  url(r'^directions/group_confirm_get$', group_confirm_get),
                  url(r'^direction/researches/update$', update_direction),
                  url(r'^direction/researches/cancel$', cancel_direction),
                  url(r'^direction/researches/update/history$', load_history),
                  url(r'^direction/researches/update/history/print$', print_history),
                  url(r'^directory/tubes/all$', get_all_tubes),
                  url(r'^directory/tubes$', tubes_control),
                  url(r'^directory/tubes/relation$', tubes_relation),
                  url(r'^directory/research$', directory_research),
                  url(r'^directory/researches$', directory_researches),
                  url(r'^directory/researches/sort$', directory_researches_update_sort),
                  url(r'^directory/researches/hide/toggle$', directory_toggle_hide_research),
                  url(r'^directory/researches/copy$', directory_copy_research),
                  url(r'^directory/researches/group$', directory_researches_group),
                  url(r'^directory/researches/directions$', directory_get_directions),
                  url(r'^directory/researches/list$', directory_researches_list),
                  url(r'^directory/researches/update_uet$', directory_researches_update_uet),
                  url(r'^directory/researches/update_mode$', directory_researches_update_mode),
                  url(r'^directory/researches/update_template$', researches_update_template),
                  url(r'^researches/ajax/search$', ajax_search_res),
                  url(r'^researches/get/one$', researches_get_one),
                  url(r'^dashboard/', include('dashboard.urls')),
                  url(r'^dashboard/receive$', receive),
                  url(r'^dashboard/receive/one_by_one$', receive_obo),
                  url(r'^dashboard/receive/last_received$', last_received),
                  url(r'^dashboard/receive/execlist$', receive_execlist),
                  url(r'^dashboard/receive/history$', receive_history),
                  url(r'^dashboard/receive/journal$', receive_journal),
                  url(r'^tubes/get$', tubes_get),
                  url(r'^results/search$', results_search),
                  url(r'^results/search/directions$', results_search_directions),
                  url(r'^results/enter$', enter),
                  url(r'^results/save$', results_save),
                  url(r'^results/loadready$', loadready),
                  url(r'^results/get$', result_get),
                  url(r'^results/get/full$', get_full_result),
                  url(r'^results/get/odf$', get_odf_result),
                  url(r'^results/conformation$', result_conformation),
                  url(r'^results/confirm$', result_confirm),
                  url(r'^results/confirm/list$', result_confirm_list),
                  url(r'^results/pdf$', result_print),
                  url(r'^results/html$', result_html),
                  url(r'^results/journal$', result_journal_print),
                  url(r'^results/filter$', result_filter),
                  url(r'^results/day$', get_day_results),
                  url(r'^statistic$', statistic_page),
                  url(r'^statistic/xls$', statistic_xls),
                  url(r'^ajax_select/', include(ajax_select_urls)),
                  url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                  url(r'^admin/', include(admin.site.urls)),
                  url(r'^construct/', include(urls.urlpatterns)),
                  url(r'^api/', include(api_urls.urlpatterns)),
                  url(r'^barcodes/', include(barcodes_urls.urlpatterns)),
                  url(r'^logout/$', logout, {'next_page': '/'})
              ] + staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
