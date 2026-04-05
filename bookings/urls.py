from django.urls import path
from . import views

urlpatterns = [
    # Page
    path('calendar/',               views.calendar_view,        name='calendar'),

    # DRF API
    path('api/slots/',              views.api_slots,            name='api_slots'),
    path('api/create/',             views.api_create_booking,   name='api_create_booking'),
    path('api/mine/',               views.api_my_bookings,      name='api_my_bookings'),
    path('api/<int:booking_id>/cancel/', views.api_cancel_booking,  name='api_cancel_booking'),
    path('api/<int:booking_id>/status/', views.api_update_status,   name='api_update_status'),
]
