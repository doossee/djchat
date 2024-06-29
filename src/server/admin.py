from django.contrib import admin

from .models import Category, Server, Channel


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    pass


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    pass
