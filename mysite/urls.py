from django.contrib import admin
from django.urls import path, include
from website.views import *
from django.urls import re_path
from mysite import settings
from django.views.static import serve
from website import views

urlpatterns = [
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}, name='static'),
    path('monitor_sheet/', monitor_sheet),
    path('monitor_sheet_insert/', monitor_sheet_insert),
    path('monitor_table/', monitor_table),
    path('select_station/', select_station),
    path('save_selected_stations/', save_selected_stations),
    path('notify_condition/', notify_condition),
    path('save_rainfall_condition/', save_rainfall_condition),
    path('valve_table/', valve_table),
    path('notify_line/', notify_line),
    path('save_line_api/', save_line_api),
    path('delete_valve_record/', delete_valve_record),

]
