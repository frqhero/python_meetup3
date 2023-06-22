from django.contrib import admin
from .models import Meetup


@admin.register(Meetup)
class MeetupAdmin(admin.ModelAdmin):
    pass
