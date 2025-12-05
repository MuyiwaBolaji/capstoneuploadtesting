from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('upload/', views.upload_view, name='upload'),
    path('files/', views.file_list_view, name='file_list'),
    path('files/<int:file_id>/', views.file_detail_view, name='file_detail'),
    path('files/<int:file_id>/process/', views.process_file_view, name='process_file'),
    path('files/<int:file_id>/visualize/', views.visualize_file_view, name='visualize_file'),
    path('files/<int:file_id>/delete/', views.delete_file_view, name='delete_file'),
    path('files/<int:file_id>/forecast/', views.forecast_data_view, name='forecast_data'),
    path('files/<int:file_id>/remove-column/', views.remove_column_view, name='remove_column'),
    path('files/<int:file_id>/remove-null-records/', views.remove_null_records_view, name='remove_null_records'),
]
