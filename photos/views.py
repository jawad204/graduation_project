from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from bookings.models import Booking
from .models import Photo
from .serializers import PhotoSerializer, PhotoUploadSerializer, PhotoCustomerSerializer
from core.decorators import photographer_required, customer_required


def run_ml_pipeline(photo):
    """
    Calls the ML pipeline on a photo and saves the result.
    Stores features, confidence, issues, use_case, and ai/final result.
    Falls back to 'pending' if models are not loaded yet.
    """
    try:
        import pipeline
        result = pipeline.predict(photo.image.path)

        # Store the full feature dict + extra metadata in the JSON field
        photo.features = {
            'values':     result.get('features', {}),
            'confidence': result.get('confidence', 0.0),
            'issues':     result.get('issues', []),
        }
        photo.use_case     = result.get('use_case', 'general')
        photo.ai_result    = result['result']
        photo.final_result = result['result']
        photo.save()

        conf = result.get('confidence', 0)
        print(f'[ML] Photo {photo.id} → {result["result"]} '
              f'({conf:.0%} confidence, use_case={result["use_case"]})')

    except Exception as e:
        print(f'[ML] Pipeline error: {e}')
        photo.ai_result    = 'pending'
        photo.final_result = 'pending'
        photo.save()


# ─── Page Views ────────────────────────────────────────────────────

@login_required
@photographer_required
def photographer_booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    photos  = Photo.objects.filter(booking=booking)
    return render(request, 'photos/photographer_gallery.html', {
        'booking': booking,
        'photos':  photos,
    })


@login_required
@customer_required
def customer_gallery(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    photos  = Photo.objects.filter(booking=booking, final_result='pass')
    return render(request, 'photos/customer_gallery.html', {
        'booking': booking,
        'photos':  photos,
    })


# ─── DRF API Views ─────────────────────────────────────────────────

@api_view(['POST'])
@parser_classes([MultiPartParser])
@photographer_required
def api_upload_photos(request, booking_id):
    """
    POST /api/photos/upload/<booking_id>/
    Photographer uploads one or more photos for a booking.
    Each photo is automatically processed by the ML pipeline.
    Body: multipart/form-data with key 'images' (multiple files)
    """
    booking = get_object_or_404(Booking, id=booking_id)
    files   = request.FILES.getlist('images')

    if not files:
        return Response({'error': 'No files provided.'}, status=status.HTTP_400_BAD_REQUEST)

    created = []
    for f in files:
        serializer = PhotoUploadSerializer(data={'image': f})
        if serializer.is_valid():
            photo = serializer.save(booking=booking)
            run_ml_pipeline(photo)
            created.append(PhotoSerializer(photo, context={'request': request}).data)

    return Response({'uploaded': len(created), 'photos': created}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@photographer_required
def api_booking_photos(request, booking_id):
    """
    GET /api/photos/booking/<booking_id>/
    Returns all photos for a booking (photographer view — all results shown).
    """
    booking = get_object_or_404(Booking, id=booking_id)
    photos  = Photo.objects.filter(booking=booking)
    serializer = PhotoSerializer(photos, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['PATCH'])
@photographer_required
def api_override_photo(request, photo_id):
    """
    PATCH /api/photos/<photo_id>/override/
    Photographer manually approves or rejects a photo.
    Body: { action: 'approve' | 'reject' }
    """
    photo  = get_object_or_404(Photo, id=photo_id)
    action = request.data.get('action')

    if action == 'approve':
        photo.final_result             = 'pass'
        photo.override_by_photographer = True
        photo.save()
    elif action == 'reject':
        photo.final_result             = 'fail'
        photo.override_by_photographer = True
        photo.save()
    else:
        return Response({'error': 'action must be approve or reject'}, status=400)

    serializer = PhotoSerializer(photo, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@customer_required
def api_customer_photos(request, booking_id):
    """
    GET /api/photos/my/<booking_id>/
    Returns only passing photos for a booking (customer view).
    """
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    photos  = Photo.objects.filter(booking=booking, final_result='pass')
    serializer = PhotoCustomerSerializer(photos, many=True, context={'request': request})
    return Response(serializer.data)
