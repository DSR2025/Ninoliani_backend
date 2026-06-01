from django.core.paginator import InvalidPage, Paginator
from django.db.models.functions import Coalesce
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from .models import Category, Collection, Product


def home_view(request):
    return render(request, "index.html")


def unique_nonempty_values(values):
    return sorted({value.strip() for value in values if value.strip()})


def build_sort_url(request, sort):
    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_params.pop("ajax", None)
    query_params["sort"] = sort
    return f"?{query_params.urlencode()}"


def build_page_url(request, page):
    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_params.pop("ajax", None)
    query_params["page"] = page
    return f"?{query_params.urlencode()}"


def catalog_view(request):
    category_slug = request.GET.get("category")
    collection_slug = request.GET.get("collection")
    selected_colors = request.GET.getlist("color")
    selected_product_types = request.GET.getlist("product_type")
    selected_sort = request.GET.get("sort", "featured")

    if selected_sort not in {"featured", "price_asc", "price_desc"}:
        selected_sort = "featured"

    if category_slug and collection_slug:
        raise Http404

    collections = Collection.objects.all().order_by("name")
    active_category_slug = ""
    active_collection_slug = ""

    if collection_slug:
        collection = get_object_or_404(Collection, slug=collection_slug)
        products = Product.objects.filter(collection=collection, is_active=True)
        active_collection_slug = collection.slug
        catalog_title = collection.name
        catalog_subtitle = "Ύδρα" if collection.slug == "hydra" else ""
    else:
        category = get_object_or_404(Category, slug=category_slug or "new-arrivals")
        if category.slug == "collections" or category.children.exists():
            raise Http404

        products = Product.objects.filter(categories=category, is_active=True)
        active_category_slug = category.slug
        catalog_title = category.name
        catalog_subtitle = ""

    available_colors = unique_nonempty_values(
        products.values_list("color", flat=True)
    )
    available_product_types = unique_nonempty_values(
        products.values_list("product_type", flat=True)
    )

    if selected_colors:
        products = products.filter(color__in=selected_colors)
    if selected_product_types:
        products = products.filter(product_type__in=selected_product_types)

    products = products.annotate(
        actual_price=Coalesce("discount_price", "price")
    )

    if selected_sort == "price_asc":
        products = products.order_by("actual_price", "-created_at")
    elif selected_sort == "price_desc":
        products = products.order_by("-actual_price", "-created_at")
    else:
        products = products.order_by("-created_at")

    products = products.prefetch_related("images")

    paginator = Paginator(products, 24)
    try:
        page_obj = paginator.page(request.GET.get("page", 1))
    except InvalidPage as error:
        raise Http404 from error

    query_params_without_page = request.GET.copy()
    query_params_without_page.pop("page", None)
    query_params_without_page.pop("ajax", None)
    query_params_without_page = query_params_without_page.urlencode()
    pagination_query_prefix = (
        f"{query_params_without_page}&" if query_params_without_page else ""
    )
    next_page_url = (
        build_page_url(request, page_obj.next_page_number())
        if page_obj.has_next()
        else ""
    )
    previous_page_url = (
        build_page_url(request, page_obj.previous_page_number())
        if page_obj.has_previous()
        else ""
    )

    if (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or request.GET.get("ajax") == "1"
    ):
        return JsonResponse(
            {
                "current_page": page_obj.number,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "html": render_to_string(
                    "partials/product_card.html",
                    {"products": page_obj},
                    request=request,
                ),
                "next_page_url": next_page_url,
                "previous_page_url": previous_page_url,
                "total_pages": paginator.num_pages,
            }
        )

    return render(
        request,
        "catalog.html",
        {
            "active_category_slug": active_category_slug,
            "active_collection_slug": active_collection_slug,
            "available_colors": available_colors,
            "available_product_types": available_product_types,
            "catalog_subtitle": catalog_subtitle,
            "catalog_title": catalog_title,
            "collections": collections,
            "is_paginated": page_obj.has_other_pages(),
            "next_page_url": next_page_url,
            "page_obj": page_obj,
            "pagination_query_prefix": pagination_query_prefix,
            "paginator": paginator,
            "products": page_obj,
            "query_params_without_page": query_params_without_page,
            "selected_colors": selected_colors,
            "selected_product_types": selected_product_types,
            "selected_sort": selected_sort,
            "sort_featured_url": build_sort_url(request, "featured"),
            "sort_price_asc_url": build_sort_url(request, "price_asc"),
            "sort_price_desc_url": build_sort_url(request, "price_desc"),
        },
    )


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.order_by("sort_order", "created_at", "pk")

    return render(
        request,
        "card.html",
        {
            "images": images,
            "main_image": images.first(),
            "product": product,
        },
    )
