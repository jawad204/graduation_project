from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """Serializes the Profile model (role, phone)."""
    class Meta:
        model  = Profile
        fields = ['role', 'phone']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes User + nested Profile.
    Used in the API to return user info.
    """
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'profile']


class RegisterSerializer(serializers.Serializer):
    """
    Handles registration input validation.
    Checks that username is unique and passwords match.
    """
    username  = serializers.CharField(max_length=150)
    email     = serializers.EmailField()
    phone     = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password  = serializers.CharField(min_length=4, write_only=True)
    password2 = serializers.CharField(min_length=4, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already taken.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError('Passwords do not match.')
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username = validated_data['username'],
            email    = validated_data['email'],
            password = validated_data['password'],
        )
        user.profile.phone = validated_data.get('phone', '')
        user.profile.role  = 'customer'
        user.profile.save()
        return user
