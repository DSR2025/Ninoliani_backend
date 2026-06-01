import logging

from django.core.paginator import InvalidPage, Paginator
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.functions import Coalesce
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .models import Category, Collection, Product


logger = logging.getLogger(__name__)


def home_view(request):
    collections = Collection.objects.filter(is_active=True).order_by(
        "sort_order",
        "name",
    )
    return render(request, "index.html", {"collections": collections})


@require_POST
def contact_view(request):
    form = ContactForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "errors": {
                    field: errors[0]
                    for field, errors in form.errors.items()
                },
            },
            status=400,
        )

    data = form.cleaned_data
    message = "\n".join(
        [
            f"Name: {data['fullName']}",
            f"Phone: {data['phone']}",
            f"Email: {data['email']}",
            f"Comment: {data['comment']}",
        ]
    )

    try:
        sent_messages = send_mail(
            subject="New contact request from Ninoliani",
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.CONTACT_EMAIL_TO],
            fail_silently=False,
        )
        if sent_messages != 1:
            raise RuntimeError("Contact email was not sent")
    except Exception as error:
        print("CONTACT EMAIL ERROR:", type(error).__name__, str(error), flush=True)
        logger.exception("Contact email sending failed")
        return JsonResponse(
            {
                "ok": False,
                "error": "Email sending failed",
            },
            status=500,
        )

    return JsonResponse(
        {
            "ok": True,
            "message": "Message sent successfully",
        }
    )


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

    collections = Collection.objects.filter(is_active=True).order_by("sort_order", "name")
    active_category_slug = ""
    active_collection_slug = ""

    if collection_slug:
        collection = get_object_or_404(Collection, slug=collection_slug)
        products = Product.objects.filter(collection=collection, is_active=True)
        active_collection_slug = collection.slug
        catalog_title = collection.name
        catalog_subtitle = collection.greek_title
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
