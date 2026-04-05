from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .serializers import RegisterSerializer, UserSerializer
from .decorators import photographer_required, customer_required


# ─── Page Views (render HTML templates) ───────────────────────────

def home(request):
    """Redirect to the right dashboard based on role."""
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.profile.is_photographer():
        return redirect('photographer_dashboard')
    return redirect('customer_dashboard')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user:
            login(request, user)
            return redirect('home')
        error = 'Wrong username or password.'
    return render(request, 'core/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/register.html')


@login_required
@customer_required
def customer_dashboard(request):
    from bookings.models import Booking
    bookings = Booking.objects.filter(customer=request.user).order_by('-session_date')
    return render(request, 'core/customer_dashboard.html', {'bookings': bookings})


@login_required
@photographer_required
def photographer_dashboard(request):
    from bookings.models import Booking
    bookings = Booking.objects.all().order_by('-session_date')
    return render(request, 'core/photographer_dashboard.html', {'bookings': bookings})


# ─── DRF API Views ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """
    POST /api/register/
    Accepts: { username, email, password, password2, phone }
    Returns: { id, username, email, profile }
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def api_current_user(request):
    """
    GET /api/me/
    Returns the currently logged-in user's info.
    """
    return Response(UserSerializer(request.user).data)
