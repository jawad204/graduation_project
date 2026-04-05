from rest_framework import serializers
from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    """
    Full booking serializer.
    customer_name is a read-only computed field (we don't want
    the frontend to send a name, we read it from the logged-in user).
    """
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model  = Booking
        fields = [
            'id',
            'customer_name',
            'session_date',
            'session_time',
            'status',
            'notes',
            'created_at',
        ]
        # customer and created_at are set automatically, not by the user
        read_only_fields = ['id', 'customer_name', 'created_at']

    def get_customer_name(self, obj):
        return obj.customer.username

    def validate(self, data):
        """
        Check the slot is not already taken before saving.
        This runs when creating a new booking.
        """
        date = data.get('session_date')
        time = data.get('session_time')
        if Booking.objects.filter(session_date=date, session_time=time).exists():
            raise serializers.ValidationError('This time slot is already booked.')
        return data


class BookingCalendarSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer just for the calendar view.
    Returns only what FullCalendar needs.
    """
    title      = serializers.SerializerMethodField()
    start      = serializers.SerializerMethodField()
    color      = serializers.SerializerMethodField()
    is_mine    = serializers.SerializerMethodField()

    class Meta:
        model  = Booking
        fields = ['id', 'title', 'start', 'color', 'status', 'is_mine']

    def get_title(self, obj):
        request = self.context.get('request')
        if request and obj.customer == request.user:
            return 'My Session'
        return 'Booked'

    def get_start(self, obj):
        return f'{obj.session_date}T{obj.session_time}'

    def get_color(self, obj):
        request = self.context.get('request')
        if request and obj.customer == request.user:
            return '#2563eb'   # blue = mine
        return '#ef4444'       # red = taken by someone else

    def get_is_mine(self, obj):
        request = self.context.get('request')
        return request and obj.customer == request.user
