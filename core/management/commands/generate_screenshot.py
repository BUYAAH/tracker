from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from core.models import Screenshot
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import time


class Command(BaseCommand):
    help = 'Generate a screenshot of the family tracker'

    def handle(self, *args, **options):
        self.stdout.write('Starting screenshot generation...')
        
        try:
            # Chrome options for headless browsing
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=480,800")

            self.stdout.write('Initializing Chrome driver...')
            driver = webdriver.Chrome(options=chrome_options)

            # Determine URL based on environment
            if settings.DEBUG:
                protocol = "http"
                current_site = "127.0.0.1:8000"
            else:
                protocol = 'https'
                current_site = "patronum.eu.pythonanywhere.com"
            
            url = f"{protocol}://{current_site}/"
            self.stdout.write(f'Loading URL: {url}')

            try:
                driver.get(url)
                self.stdout.write('Page loaded, waiting for content...')

                # Wait for Leaflet map to load
                time.sleep(10)  # Wait for Leaflet to fully load

                # Wait for content div
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "content"))
                )
                self.stdout.write('Content div found!')

                # Take screenshot
                element = driver.find_element(By.ID, "content")
                element_screenshot = element.screenshot_as_png
                self.stdout.write('Screenshot captured!')

                # Convert to BMP
                image = Image.open(BytesIO(element_screenshot))
                output = BytesIO()
                image.save(output, format="BMP")
                output.seek(0)

                # Save to model
                screenshot = Screenshot()
                filename = f'family-tracker-{int(time.time())}.bmp'
                screenshot.image.save(
                    filename,
                    ContentFile(output.getvalue()),
                    save=False  # Don't save the model yet
                )
                screenshot.save()  # Now save the model
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Screenshot saved successfully! ID: {screenshot.id}, File: {screenshot.image.name}'
                    )
                )
                
                # Verify file exists
                import os
                full_path = screenshot.image.path
                if os.path.exists(full_path):
                    self.stdout.write(f'File confirmed at: {full_path}')
                else:
                    self.stdout.write(self.style.WARNING(f'File NOT found at: {full_path}'))

            finally:
                driver.quit()
                self.stdout.write('Chrome driver closed.')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating screenshot: {str(e)}')
            )