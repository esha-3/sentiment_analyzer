from django.urls import path
from . import views

app_name = 'proj'

urlpatterns = [
    path('', views.index, name='index'),
    path('analyze/', views.analyze, name='analyze'),
    path('history/', views.history, name='history'),
    path('delete/<int:pk>/', views.delete_analysis, name='delete_analysis'),
    path('clear-all/', views.clear_all, name='clear_all'),
]
