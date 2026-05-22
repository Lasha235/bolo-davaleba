from django.contrib import admin
from .models import (
    Category,
    Tag,
    Event,
    Registration,
    Review,
    EventMedia,
)

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Event)
admin.site.register(Registration)
admin.site.register(Review)
admin.site.register(EventMedia)