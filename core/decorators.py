from django.shortcuts import redirect
from functools import wraps


def photographer_required(view_func):
    """Only lets photographers through. Redirects others."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.profile.role != 'photographer':
            return redirect('customer_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def customer_required(view_func):
    """Only lets customers through. Redirects others."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.profile.role != 'customer':
            return redirect('photographer_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
