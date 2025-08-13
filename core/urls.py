from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.map_view, name='map'),
    path('api/', views.owntracks_api, name='owntracks_api'),
]