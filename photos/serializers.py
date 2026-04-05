from rest_framework import serializers
from .models import Photo


class PhotoSerializer(serializers.ModelSerializer):
    """
    Full photo serializer — used in the photographer's view.
    Exposes AI result, confidence, detected issues, and override status.
    """
    image_url  = serializers.SerializerMethodField()
    confidence = serializers.SerializerMethodField()
    issues     = serializers.SerializerMethodField()

    class Meta:
        model  = Photo
        fields = [
            'id',
            'booking',
            'image_url',
            'use_case',
            'ai_result',
            'final_result',
            'confidence',
            'issues',
            'override_by_photographer',
            'uploaded_at',
        ]
        read_only_fields = [
            'id', 'image_url', 'use_case',
            'ai_result', 'confidence', 'issues', 'uploaded_at',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def get_confidence(self, obj):
        """Pull confidence from the features JSON field."""
        if obj.features and isinstance(obj.features, dict):
            return obj.features.get('confidence', None)
        return None

    def get_issues(self, obj):
        """Pull quality issues list from the features JSON field."""
        if obj.features and isinstance(obj.features, dict):
            return obj.features.get('issues', [])
        return []


class PhotoUploadSerializer(serializers.ModelSerializer):
    """
    Used when the photographer uploads a photo.
    Only requires the image file — everything else is set by the pipeline.
    """
    class Meta:
        model  = Photo
        fields = ['image']


class PhotoCustomerSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for customer gallery.
    Only shows passing photos — hides all AI details from customer.
    """
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Photo
        fields = ['id', 'image_url', 'uploaded_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url
