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
    from django.conf import settings
    from django.urls import reverse
    import time
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=480,800")

    driver = webdriver.Chrome(options=chrome_options)

    if settings.DEBUG:
        protocol = "http"
        current_site = "127.0.0.1:8000"
    else:
        protocol = 'https'
        current_site = "patronum.eu.pythonanywhere.com"
    
    url = f"{protocol}://{current_site}/"

    try:
        driver.get(url)

        time.sleep(2)  # Let Leaflet map load

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "content"))
        )

        element = driver.find_element(By.ID, "content")
        element_screenshot = element.screenshot_as_png
        image = Image.open(io.BytesIO(element_screenshot))

        output = io.BytesIO()
        image.save(output, format="BMP")
        output.seek(0)

        response = HttpResponse(output.getvalue(), content_type='image/bmp')
        response['Content-Disposition'] = 'attachment; filename="family-tracker.bmp"'
        return response

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

    finally:
        driver.quit()
