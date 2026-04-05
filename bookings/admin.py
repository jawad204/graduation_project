from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ['customer', 'session_date', 'session_time', 'status']
    list_filter   = ['status']
