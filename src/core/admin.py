from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


from core import models

# admin.TabularInline
class RecipeInline(admin.StackedInline):
    '''Tabular Inline View for Recipe'''

    model = models.Recipe
    min_num = 1
    max_num = 20
    extra = 0
    raw_id_fields = ("user",)
    fields = ("title", "price", "time_minutes")


class UserAdmin(BaseUserAdmin):
    ordering = ["id", "name"]
    list_display = ["email", "name"]

    # using in edit an object
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal Info"), {"fields": ("name",)}),
        (_("Permisions"), {"fields": ("is_active", "is_staff", "is_superuser")}),
        (_("Important Dates"), {"fields": ("last_login",)}),
    )

    readonly_fields = ("last_login",)

    # using in add a new object
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
        (_("Personal Info"), {"classes": ("wide",), "fields": ("name",)}),
        (
            _("Permisions"),
            {"classes": ("wide",), "fields": ("is_active", "is_staff", "is_superuser")},
        ),
    )
    
    inlines = [RecipeInline]


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe)