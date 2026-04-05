from django.contrib import admin
from .models import Photo

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'use_case', 'ai_result', 'final_result', 'override_by_photographer']
    list_filter  = ['ai_result', 'final_result', 'use_case']
