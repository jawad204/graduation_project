from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Booking
from .serializers import BookingSerializer, BookingCalendarSerializer
from core.decorators import customer_required, photographer_required


# ─── Page Views ────────────────────────────────────────────────────

@login_required
def calendar_view(request):
    """Renders the calendar page. Data is loaded via the API below."""
    return render(request, 'bookings/calendar.html')


# ─── DRF API Views ─────────────────────────────────────────────────

@api_view(['GET'])
def api_slots(request):
    """
    GET /api/bookings/slots/
    Returns all bookings formatted for FullCalendar.
    Used by the calendar page to show booked/available slots.
    """
    bookings = Booking.objects.exclude(status='cancelled')
    serializer = BookingCalendarSerializer(
        bookings, many=True, context={'request': request}
    )
    return Response(serializer.data)


@api_view(['POST'])
@customer_required
def api_create_booking(request):
    """
    POST /api/bookings/create/
    Body: { session_date, session_time, notes }
    Creates a new booking for the logged-in customer.
    Returns the created booking or validation errors.
    """
    serializer = BookingSerializer(data=request.data)
    if serializer.is_valid():
        try:
            serializer.save(customer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(
                {'error': 'This slot is already taken.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def api_my_bookings(request):
    """
    GET /api/bookings/mine/
    Returns all bookings for the logged-in customer.
    """
    bookings   = Booking.objects.filter(customer=request.user)
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
def api_cancel_booking(request, booking_id):
    """
    PATCH /api/bookings/<id>/cancel/
    Cancels a booking. Customer can only cancel their own.
    """
    booking = get_object_or_404(Booking, id=booking_id)

    # customers can only cancel their own bookings
    if request.user.profile.is_customer() and booking.customer != request.user:
        return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

    booking.status = 'cancelled'
    booking.save()
    return Response({'message': 'Booking cancelled.'})


@api_view(['PATCH'])
@photographer_required
def api_update_status(request, booking_id):
    """
    PATCH /api/bookings/<id>/status/
    Photographer only — update booking status.
    Body: { status: 'completed' | 'cancelled' | 'confirmed' }
    """
    booking    = get_object_or_404(Booking, id=booking_id)
    new_status = request.data.get('status')

    if new_status not in ['confirmed', 'completed', 'cancelled']:
        return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = new_status
    booking.save()
    serializer = BookingSerializer(booking)
    return Response(serializer.data)
