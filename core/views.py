from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import json
import io
import base64
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .models import Location

User = get_user_model()


def map_view(request):
    # Get latest location for each user
    latest_locations = []
    for user in User.objects.all():
        latest_location = Location.objects.filter(user=user).first()
        if latest_location:
            latest_locations.append(latest_location)
    
    context = {
        'locations': latest_locations
    }
    return render(request, 'core/map.html', context)


@csrf_exempt
def owntracks_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # OwnTracks sends data in this format
            if data.get('_type') == 'location':
                # Get or create user based on topic/username
                username = data.get('tid', 'unknown')  # tid is the tracker ID
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'first_name': username}
                )
                
                # Create location record
                Location.objects.create(
                    user=user,
                    latitude=data.get('lat'),
                    longitude=data.get('lon'),
                    accuracy=data.get('acc'),
                    battery=data.get('batt')
                )
                
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'method not allowed'}, status=405)


def screenshot_bmp(request):
    """Serve the latest screenshot as BMP"""
    from .models import Screenshot
    
    try:
        # Get the latest screenshot
        screenshot = Screenshot.objects.first()
        
        if not screenshot:
            return HttpResponse("No screenshot available. Run: python manage.py generate_screenshot", status=404)
        
        # Convert the stored image to BMP if needed
        with screenshot.image.open('rb') as img_file:
            image = Image.open(img_file)
            output = io.BytesIO()
            image.save(output, format="BMP")
            output.seek(0)
            
            response = HttpResponse(output.getvalue(), content_type='image/bmp')
            response['Content-Disposition'] = 'attachment; filename="family-tracker.bmp"'
            return response
    
    except Exception as e:
        return HttpResponse(f"Error serving screenshot: {str(e)}", status=500)
