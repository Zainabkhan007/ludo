from django.urls import path
from .views import move_piece

urlpatterns = [
    path("move/", move_piece),
]
