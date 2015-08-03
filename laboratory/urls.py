from django.conf.urls import include, url, patterns
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from users.views import home
from dashboard.views import dashboard, create_user, create_pod, directions, researches_control
from clients.views import ajax_search
from researches.views import ajax_search_res, researches_get_one, get_all_tubes, tubes_control, tubes_relation
from directions.views import dir_save, gen_pdf_dir, get_one_dir, update_direction, load_history, print_history, \
    get_issledovaniya, get_client_directions
from receivematerial.views import receive, tubes_get
from results.views import enter, loadready, results_save, result_get, result_conformation, result_confirm, result_print, \
    result_filter
from construct import urls
from directory.views import directory_researches, directory_research, directory_researches_group, \
    directory_get_directions, directory_researches_list, directory_researches_update_uet, \
    directory_researches_update_mode

urlpatterns = [
                  url(r'^$', home, name='home'),
                  url(r'^clients/ajax/search$', ajax_search),
                  url(r'^directions/ajax/save$', dir_save),
                  url(r'^directions/pdf$', gen_pdf_dir),
                  url(r'^directions/get/one$', get_one_dir),
                  url(r'^directions/get/issledovaniya', get_issledovaniya),
                  url(r'^directions/list/client$', get_client_directions),
                  url(r'^direction/researches/update$', update_direction),
                  url(r'^direction/researches/update/history$', load_history),
                  url(r'^direction/researches/update/history/print$', print_history),
                  url(r'^directory/tubes/all$', get_all_tubes),
                  url(r'^directory/tubes$', tubes_control),
                  url(r'^directory/tubes/relation$', tubes_relation),
                  url(r'^directory/research$', directory_research),
                  url(r'^directory/researches$', directory_researches),
                  url(r'^directory/researches/group$', directory_researches_group),
                  url(r'^directory/researches/directions$', directory_get_directions),
                  url(r'^directory/researches/list$', directory_researches_list),
                  url(r'^directory/researches/update_uet$', directory_researches_update_uet),
                  url(r'^directory/researches/update_mode$', directory_researches_update_mode),
                  url(r'^researches/ajax/search$', ajax_search_res),
                  url(r'^researches/control$', researches_control),
                  url(r'^researches/get/one', researches_get_one),
                  url(r'^dashboard/$', dashboard),
                  url(r'^dashboard/create_user$', create_user),
                  url(r'^dashboard/create_podr$', create_pod),
                  url(r'^dashboard/directions$', directions),
                  url(r'^dashboard/receive', receive),
                  url(r'^tubes/get', tubes_get),
                  url(r'^results/enter', enter),
                  url(r'^results/save', results_save),
                  url(r'^results/loadready', loadready),
                  url(r'^results/get', result_get),
                  url(r'^results/conformation$', result_conformation),
                  url(r'^results/confirm$', result_confirm),
                  url(r'^results/pdf', result_print),
                  url(r'^results/filter$', result_filter),
                  url(r'^admin/', include(admin.site.urls)),
                  url(r'^construct/', include(urls.urlpatterns)),
                  url(r'^logout/$', 'django.contrib.auth.views.logout',
                      {'next_page': '/'}),
              ] + staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)),
                            )
