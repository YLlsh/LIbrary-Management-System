"""
URL configuration for l project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from borrow.views import *

urlpatterns = [
    path('',home, name='home' ),
    path('login/', log, name='login'),
    path('log_out', log_out, name='log_out'),
    path('book/<id>/', b, name='b'),
    path('student/<id>/', student, name='student'),
    path('add_student/', add_student, name='add_student'),
    path('add_book/', add_book, name='add_book'),
    path('delete/<id>/', return_book, name='delete_item'),
    path('re_issue/<id>/', re_issue, name='re_issue'),
    path('student_info/',student_info, name='student_info'),
    path('borrow/',borrow, name='borrow' ),
    path('chat_bot/',chat_bot, name='chat_bot' ),
    path('admin/', admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)