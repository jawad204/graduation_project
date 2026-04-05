from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('booking/<int:booking_id>/',  views.photographer_booking_detail, name='photographer_booking_detail'),
    path('gallery/<int:booking_id>/',  views.customer_gallery,            name='customer_gallery'),

    # DRF API
    path('api/upload/<int:booking_id>/',  views.api_upload_photos,    name='api_upload_photos'),
    path('api/booking/<int:booking_id>/', views.api_booking_photos,   name='api_booking_photos'),
    path('api/<int:photo_id>/override/',  views.api_override_photo,   name='api_override_photo'),
    path('api/my/<int:booking_id>/',      views.api_customer_photos,  name='api_customer_photos'),
]
