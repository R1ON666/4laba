from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.add_book, name="add"),
    path("upload/", views.upload, name="upload"),
    path("download/<str:file_id>/", views.download, name="download"),
    path("export/", views.export_all, name="export_all"),
    path("db/search/", views.book_search, name="book_search"),
    path("db/<int:pk>/edit/", views.book_edit, name="book_edit"),
    path("db/<int:pk>/delete/", views.book_delete, name="book_delete"),
]
