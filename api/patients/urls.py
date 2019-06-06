from django.urls import path
from . import views

urlpatterns = [
    path('search-card', views.patients_search_card),
    path('search-individual', views.patients_search_individual),
    path('search-l2-card', views.patients_search_l2_card),
    path('card/<int:card_id>', views.patients_get_card_data),
    path('card/save', views.patients_card_save),
    path('individuals/search', views.individual_search),
    path('individuals/sex', views.get_sex_by_param),
    path('individuals/edit-doc', views.edit_doc),
    path('individuals/edit-agent', views.edit_agent),
    path('individuals/update-cdu', views.update_cdu),
    path('individuals/update-wia', views.update_wia),
    path('individuals/sync-rmis', views.sync_rmis),
    path('individuals/load-anamnesis', views.load_anamnesis),
    path('individuals/load-dreg', views.load_dreg),
    path('individuals/load-benefit', views.load_benefit),
    path('individuals/load-dreg-detail', views.load_dreg_detail),
    path('individuals/load-benefit-detail', views.load_benefit_detail),
    path('individuals/save-dreg', views.save_dreg),
    path('individuals/save-benefit', views.save_benefit),
    path('individuals/save-anamnesis', views.save_anamnesis),
]