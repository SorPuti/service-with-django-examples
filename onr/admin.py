from django.contrib import admin
from .models import OnrModel


@admin.register(OnrModel)
class OnrModelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "status", "owner", "updated_at")
    list_filter = ("status",)
    search_fields = ("name", "code", "owner__username")
