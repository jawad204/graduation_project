from django.db import models
from bookings.models import Booking


class Photo(models.Model):
    RESULT_CHOICES = [
        ('pending', 'Pending'),
        ('pass',    'Pass'),
        ('fail',    'Fail'),
    ]

    booking                  = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='photos')
    image                    = models.ImageField(upload_to='photos/%Y/%m/')
    # ML results stored as JSON in the database
    features                 = models.JSONField(null=True, blank=True)
    use_case                 = models.CharField(max_length=50, blank=True)
    ai_result                = models.CharField(max_length=10, choices=RESULT_CHOICES, default='pending')
    final_result             = models.CharField(max_length=10, choices=RESULT_CHOICES, default='pending')
    override_by_photographer = models.BooleanField(default=False)
    uploaded_at              = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Photo {self.id} | Booking {self.booking.id} | {self.final_result}'

    def visible_to_customer(self):
        return self.final_result == 'pass'
