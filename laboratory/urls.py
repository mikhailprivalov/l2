from django.conf.urls import include, url, patterns
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from users.views import home
from dashboard.views import dashboard, create_user, create_pod, directions, researches_control
from clients.views import ajax_search
from researches.views import ajax_search_res, researches_get_one, get_all_tubes, tubes_control
from directions.views import dir_save, gen_pdf_dir, get_one_dir, update_direction, load_history, print_history, \
    get_issledovaniya
from receivematerial.views import receive, tubes_get
from results.views import enter, loadready
from construct import urls

urlpatterns = [
                  url(r'^$', home, name='home'),
                  url(r'^clients/ajax/search$', ajax_search),
                  url(r'^directions/ajax/save$', dir_save),
                  url(r'^directions/pdf$', gen_pdf_dir),
                  url(r'^directions/get/one$', get_one_dir),
                  url(r'^directions/get/issledovaniya', get_issledovaniya),
                  url(r'^direction/researches/update$', update_direction),
                  url(r'^direction/researches/update/history$', load_history),
                  url(r'^direction/researches/update/history/print$', print_history),
                  url(r'^directory/tubes/all$', get_all_tubes),
                  url(r'^directory/tubes$', tubes_control),
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
                  url(r'^results/loadready', loadready),
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
