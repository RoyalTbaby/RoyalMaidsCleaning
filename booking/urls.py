from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('select-maid/', views.select_maid, name='select_maid'),
    path('select-schedule/<int:maid_id>/', views.select_schedule, name='select_schedule'),
    path('get-availability/<int:maid_id>/<str:date>/', views.get_availability, name='get_availability'),
    path('personal-info/', views.personal_info, name='personal_info'),
    path('confirmation/', views.confirmation, name='confirmation'),
    path('test-email/', views.test_email, name='test_email'),
]
