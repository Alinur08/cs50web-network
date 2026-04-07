from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
import json
from .models import User,Post

def json_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                "error": "login required"
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

def index(request):
    return render(request, "network/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
def create_post(request):
    if request.method == "POST":
        data = json.loads(request.body)
        content = data.get("content")
        if(len(content)==0):
            return JsonResponse({"message":"Empty Content"})
        

        post = Post.objects.create(
            user=request.user,
            content=content
        )

        return JsonResponse({
            "message": "Post created",
            "content": post.content
        })
def get_posts(request):
    following=request.GET.get("following")
    posts=[]
    if following == "true":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required"}, status=403)
        following_users = request.user.following.all()
        posts = Post.objects.filter(user__in=following_users).order_by("-timestamp")
    else:
        posts = Post.objects.all().order_by("-timestamp")

    paginator = Paginator(posts, 5)
    page_number = request.GET.get("page")
    page_data = paginator.get_page(page_number)

    data = []

    for post in page_data:
        data.append({
            "id": post.id,
            "user": post.user.username,
            "content": post.content,
            "timestamp": post.timestamp.strftime("%Y-%m-%d %H:%M"),
            "likes_count":len(post.likes.all()),
            "is_liked":post.likes.filter(id=request.user.id).exists()
            
        })

    return JsonResponse({
        "posts": data,
        "next": page_data.has_next(),
        "previous": page_data.has_previous()
    })

    following_users=request.user.following.all()
    posts = Post.objects.filter(user__in =following_users).order_by("-timestamp")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_data = paginator.get_page(page_number)

    data = []

    for post in page_data:
        data.append({
            "id": post.id,
            "user": post.user.username,
            "content": post.content,
            "timestamp": post.timestamp.strftime("%Y-%m-%d %H:%M"),
            "likes_count":len(post.likes.all()),
            "is_liked":post.likes.filter(id=request.user.id).exists()
            
        })

    return JsonResponse({
        "posts": data,
        "next": page_data.has_next(),
        "previous": page_data.has_previous()
    })
def profile(request, username):
    user_profile = User.objects.get(username=username)
    
    posts =user_profile.posts.order_by("-timestamp")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_data = paginator.get_page(page_number)

    # followers count
    followers_count = user_profile.followers.count()

    # following count
    following_count = user_profile.following.count()

    # check if current user follows this profile
    is_following = False
    if request.user.is_authenticated:
        is_following = request.user.following.filter(id=user_profile.id).exists()

    return JsonResponse({
        "profile_user": {"id":user_profile.id,"username":user_profile.username},
        "posts": [
            {
            "id": post.id,
            "user": post.user.username,
            "content": post.content,
            "timestamp": post.timestamp.strftime("%Y-%m-%d %H:%M"),
            "likes_count":len(post.likes.all()),
            "is_liked":post.likes.filter(id=request.user.id).exists()
            }
            for post in page_data
        ],
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following,
        "has_next": page_data.has_next(),
        "has_previous": page_data.has_previous(),
    })
@json_login_required
def edit_post(request, post_id):
    if request.method == "PUT":
        post = Post.objects.get(id=post_id)

        # security check
        if post.user != request.user:
            return JsonResponse({"error": "Not allowed"}, status=403)

        data = json.loads(request.body)
        new_content = data.get("content")

        if new_content.strip() == "":
            return JsonResponse({"error": "Empty content"}, status=400)

        post.content = new_content
        post.save()

        return JsonResponse({
            "success": True,
            "content": post.content
        })
@json_login_required
def follow(request, user_id):

    if request.method == "PUT":
        if request.user.id==user_id:
            return JsonResponse({"success":False},status=403)
        target = User.objects.get(id=user_id)
        followed=False
        if target in request.user.following.all():
            request.user.following.remove(target)
        else:
            request.user.following.add(target)
            followed = True

        return JsonResponse({
            "success": True,
            "following": followed,
            "followers_count": target.followers.count()
        })
@json_login_required
def like(request, post_id):
    if request.method == "PUT":
        post = Post.objects.get(id=post_id)
        user = request.user

        if user in post.likes.all():
            post.likes.remove(user)
            liked = False
        else:
            post.likes.add(user)
            liked = True

        return JsonResponse({
            "success": True,
            "liked": liked,
            "likes_count": post.likes.count()
        })
    
