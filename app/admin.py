from django.contrib import admin

from .models import (Subnet,
                     SubnetParent,
                     Middleware,
                     DnsEntry,
                     DnsPoolEntry,
                     DnsNameComponentCategory,
                     DnsNameComponent,
                     DnsNamePattern,
                     DnsNameVariation)

# Register your models here.

class DnsNameComponentAdmin(admin.ModelAdmin):
    list_display = ('component', 'component_category')


class DnsNamePatternAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Subnet)
admin.site.register(SubnetParent)
admin.site.register(Middleware)
admin.site.register(DnsEntry)
admin.site.register(DnsPoolEntry)
admin.site.register(DnsNameComponent, DnsNameComponentAdmin)
admin.site.register(DnsNameComponentCategory)
admin.site.register(DnsNamePattern, DnsNamePatternAdmin)
admin.site.register(DnsNameVariation)
