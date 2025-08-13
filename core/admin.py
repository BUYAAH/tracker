from django.contrib import admin
from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'timestamp', 'accuracy', 'battery')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
