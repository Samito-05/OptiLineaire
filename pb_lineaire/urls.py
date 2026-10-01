from django.urls import path
from . import views

app_name = "pb_lineaire"

urlpatterns = [
    path("", views.index, name="index"),
    path("solve/", views.solve, name="solve"),
]
