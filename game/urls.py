from django.urls import path
from . import views as v
urlpatterns = [
    path("", v.home, name="home"),
    path("room/<code>/", v.room, name="room"),
    path("room/<code>/ping/", v.ping, name="ping"),
    path("roles/", v.RoleList.as_view(), name="roles"),
    path("roles/add/", v.RoleCreate.as_view(), name="role-add"),
    path("roles/<int:pk>/", v.RoleUpdate.as_view(), name="role-edit"),
    path("roles/<int:pk>/delete/", v.RoleDelete.as_view(), name="role-delete"),
    path("rules/", v.RuleList.as_view(), name="rules"),
    path("rules/add/", v.RuleCreate.as_view(), name="rule-add"),
    path("rules/<int:pk>/", v.RuleUpdate.as_view(), name="rule-edit"),
    path("rules/<int:pk>/delete/", v.RuleDelete.as_view(), name="rule-delete"),
]
