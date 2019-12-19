from django.contrib import admin

from .models import (NameEntry,
                    NamePoolEntry,
                    NamePattern,
                    NamingScheme,
                    NameArtifacts,
                    NameArtifactsCategory)




# Register your models here.

admin.site.register(NameEntry)
admin.site.register(NamePoolEntry)
admin.site.register(NamePattern)
admin.site.register(NamingScheme)
admin.site.register(NameArtifacts)
admin.site.register(NameArtifactsCategory)
