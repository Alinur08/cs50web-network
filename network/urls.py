
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("edit/<int:post_id>", views.edit_post, name="edit_post"),
    path("create", views.create_post, name="create_post"),
    path("posts", views.get_posts, name="get_posts"),
    path("profile/<str:username>", views.profile, name="profile"),
    path("follow/<int:user_id>", views.follow, name="follow"),
    path("like/<int:post_id>", views.like, name="like"),

]
