from django.urls import path

from . import views

urlpatterns = [
    path("git-pull/", views.trigger_git_pull, name="trigger_git_pull"),
    path("git-tags/", views.trigger_git_pull, name="git_tags"),
]
