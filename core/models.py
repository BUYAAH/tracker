from django.db import models
from django.conf import settings


class Location(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    timestamp = models.DateTimeField(auto_now_add=True)
    accuracy = models.IntegerField(null=True, blank=True)
    battery = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user.username} - {self.latitude}, {self.longitude} at {self.timestamp}"


class Screenshot(models.Model):
    image = models.ImageField(upload_to='screenshots/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Screenshot {self.created_at}"
