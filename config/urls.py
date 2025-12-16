"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from web.views import index, chat_message, get_diaries, get_diary_detail, generate_diary, signup_api, login_api, logout_api, withdraw_api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index, name="home"),
    path("services/", index, {"page": "services"}, name="services"),
    path("chat/", index, {"page": "chat"}, name="chat"),
    path("diary/", index, {"page": "diary"}, name="diary"),
    
    # API endpoints
    path("api/chat/", chat_message, name="api_chat"),
    path("api/signup/", signup_api, name="api_signup"),
    path("api/login/", login_api, name="api_login"),
    path("api/logout/", logout_api, name="api_logout"),
    path("api/withdraw/", withdraw_api, name="api_withdraw"),
    path("api/diary/generate/", generate_diary, name="api_generate_diary"),
    path("api/diaries/", get_diaries, name="api_diaries"),
    path("api/diary/<str:date>/", get_diary_detail, name="api_diary_detail"),
]
