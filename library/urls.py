from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.add_book, name="add"),
    path("upload/", views.upload, name="upload"),
    path("download/<str:file_id>/", views.download, name="download"),
    path("export/", views.export_all, name="export_all"),
]
