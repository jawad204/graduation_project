@echo off
title PhotoBook v2 Setup
echo.
echo =======================================
echo   PhotoBook v2 - Setup
echo =======================================
echo.
echo [1/4] Installing dependencies...
pip install django djangorestframework pillow opencv-python scikit-learn joblib
echo.
echo [2/4] Creating database...
python manage.py makemigrations core bookings photos
python manage.py migrate
echo.
echo [3/4] Creating photographer account...
python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.filter(username='photographer').first(); u or User.objects.create_superuser('photographer','p@p.com','photo123'); u2=User.objects.get(username='photographer'); u2.profile.role='photographer'; u2.profile.save(); print('Done!')"
echo.
echo [4/4] Starting server...
echo.
echo =======================================
echo  Open: http://127.0.0.1:8000
echo  Photographer: photographer / photo123
echo  Customer: register at /register/
echo =======================================
echo.
python manage.py runserver
pause
