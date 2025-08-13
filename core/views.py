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
    """Generate a BMP screenshot of the #content div"""
    try:
        # Chrome options for headless browsing
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=480,800")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Get the full URL for the map page
            map_url = request.build_absolute_uri('/')
            
            # Load the page
            driver.get(map_url)
            
            # Wait for the content div to be present
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "content"))
            )
            
            # Wait a bit more for Leaflet map to load
            import time
            time.sleep(3)
            
            # Find the content div and take screenshot
            content_element = driver.find_element(By.ID, "content")
            screenshot_png = content_element.screenshot_as_png
            
            # Convert PNG to BMP using PIL
            png_image = Image.open(io.BytesIO(screenshot_png))
            
            # Create BMP in memory
            bmp_buffer = io.BytesIO()
            png_image.save(bmp_buffer, format='BMP')
            bmp_data = bmp_buffer.getvalue()
            
            # Return BMP as HTTP response
            response = HttpResponse(bmp_data, content_type='image/bmp')
            response['Content-Disposition'] = 'attachment; filename="family-tracker.bmp"'
            return response
            
        finally:
            driver.quit()
            
    except Exception as e:
        return HttpResponse(f"Screenshot failed: {str(e)}", status=500)
