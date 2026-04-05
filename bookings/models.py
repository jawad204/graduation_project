from django.db import models
from django.contrib.auth.models import User


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    session_date = models.DateField()
    session_time = models.TimeField()
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        # This prevents two bookings on the same date & time at the DB level
        unique_together = ('session_date', 'session_time')
        ordering = ['-session_date', '-session_time']

    def __str__(self):
        return f'{self.customer.username} | {self.session_date} {self.session_time}'

    def time_12h(self):
        return self.session_time.strftime('%I:%M %p')
