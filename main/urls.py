from django.urls import path

from . import views


urlpatterns = [
    path("", views.home_view, name="home"),
    path("catalog/", views.catalog_view, name="catalog"),
    path("product/<slug:slug>/", views.product_detail_view, name="product_detail"),
]
