from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('settings/', views.dashboard_settings, name='settings'),
    path('widgets/add/', views.add_widget, name='add_widget'),
    path('widgets/<int:widget_id>/', views.edit_widget, name='edit_widget'),
    path('widgets/<int:widget_id>/delete/', views.delete_widget, name='delete_widget'),
    path('widgets/<int:widget_id>/position/', views.update_widget_position, name='update_widget_position'),
    path('widgets/<int:widget_id>/size/', views.update_widget_size, name='update_widget_size'),
    path('widgets/<int:widget_id>/data/', views.get_widget_data, name='get_widget_data'),
    path('layout/save/', views.save_layout, name='save_layout'),
]