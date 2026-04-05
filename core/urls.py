from django.urls import path
from . import views

urlpatterns = [
    # Page routes
    path('',               views.home,                  name='home'),
    path('login/',         views.login_view,             name='login'),
    path('logout/',        views.logout_view,            name='logout'),
    path('register/',      views.register_view,          name='register'),
    path('dashboard/',     views.customer_dashboard,     name='customer_dashboard'),
    path('photographer/',  views.photographer_dashboard, name='photographer_dashboard'),

    # DRF API routes
    path('api/register/', views.api_register,            name='api_register'),
    path('api/me/',        views.api_current_user,       name='api_me'),
]
