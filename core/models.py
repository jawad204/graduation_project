from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """
    Extends Django's default User with a role.
    Every user gets a Profile automatically via signals.
    """
    ROLE_CHOICES = [
        ('customer',     'Customer'),
        ('photographer', 'Photographer'),
    ]
    user  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role  = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f'{self.user.username} — {self.role}'

    def is_photographer(self):
        return self.role == 'photographer'

    def is_customer(self):
        return self.role == 'customer'
