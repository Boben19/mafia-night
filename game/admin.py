from django.contrib import admin
from .models import Role, Rule, Game, Player

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "faction", "vote_weight", "vote_immune")
    list_filter = ("faction",)
    search_fields = ("name", "ability")

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title", "text")

admin.site.register(Game)
admin.site.register(Player)
