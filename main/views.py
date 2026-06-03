import logging
import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.exceptions import PermissionDenied
from django.core.paginator import InvalidPage, Paginator
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Prefetch
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .models import Category, Collection, CollectionImage, HomeNewArrival, Product


logger = logging.getLogger(__name__)
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def error_page_view(request, exception=None):
    status = 500
    if isinstance(exception, Http404):
        status = 404
    elif isinstance(exception, PermissionDenied):
        status = 403

    return render(request, "error.html", status=status)


def home_view(request):
    collections = (
        Collection.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "gallery_images",
                queryset=CollectionImage.objects.filter(is_active=True).order_by(
                    "sort_order",
                    "pk",
                ),
                to_attr="active_gallery_images",
            )
        )
        .order_by(
            "sort_order",
            "name",
        )
    )
    new_arrivals = (
        HomeNewArrival.objects.filter(is_active=True, product__is_active=True)
        .select_related("product")
        .prefetch_related("product__images")
        .order_by("sort_order", "pk")[:3]
    )
    return render(
        request,
        "index.html",
        {
            "canonical_url": request.build_absolute_uri(request.path),
            "collections": collections,
            "new_arrivals": new_arrivals,
            "seo_image_url": request.build_absolute_uri(
                static("img/unit1/pic1_unit1.webp")
            ),
            "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
        },
    )


def robots_txt_view(request):
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "",
            f"Sitemap: {settings.SITE_URL}/sitemap.xml",
        ]
    )
    return HttpResponse(content, content_type="text/plain")


@require_POST
def contact_view(request):
    turnstile_token = request.POST.get("cf-turnstile-response", "")
    if not verify_turnstile_token(turnstile_token, request.META.get("REMOTE_ADDR", "")):
        return JsonResponse(
            {
                "ok": False,
                "errors": {
                    "captcha": "Please complete the captcha.",
                },
            },
            status=400,
        )

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


def verify_turnstile_token(token, remote_ip=""):
    if not settings.TURNSTILE_SECRET_KEY:
        return settings.DEBUG

    if not token:
        return False

    payload = urlencode(
        {
            "secret": settings.TURNSTILE_SECRET_KEY,
            "response": token,
            "remoteip": remote_ip,
        }
    ).encode()

    try:
        request = Request(TURNSTILE_VERIFY_URL, data=payload, method="POST")
        with urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        logger.exception("Turnstile verification failed")
        return False

    return result.get("success") is True


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
        canonical_query = urlencode({"collection": collection.slug})
        seo_description = (
            collection.description[:160]
            or f"Explore {collection.name} collection by Ninoliani."
        )
        seo_image_url = (
            request.build_absolute_uri(collection.main_image.url)
            if collection.main_image
            else ""
        )
        seo_title = f"{collection.name} Collection | Ninoliani"
    else:
        category = get_object_or_404(Category, slug=category_slug or "new-arrivals")
        if category.slug == "collections" or category.children.exists():
            raise Http404

        products = Product.objects.filter(categories=category, is_active=True)
        active_category_slug = category.slug
        catalog_title = category.name
        catalog_subtitle = ""
        canonical_query = (
            urlencode({"category": category.slug})
            if category.slug != "new-arrivals"
            else ""
        )
        seo_description = f"Explore {category.name} collection by Ninoliani."
        seo_image_url = request.build_absolute_uri(
            static("img/unit1/pic1_unit1.webp")
        )
        seo_title = f"{category.name} | Ninoliani"

    canonical_url = request.build_absolute_uri(request.path)
    if canonical_query:
        canonical_url = f"{canonical_url}?{canonical_query}"

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
            "canonical_url": canonical_url,
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
            "seo_description": seo_description,
            "seo_image_url": seo_image_url,
            "seo_title": seo_title,
            "sort_featured_url": build_sort_url(request, "featured"),
            "sort_price_asc_url": build_sort_url(request, "price_asc"),
            "sort_price_desc_url": build_sort_url(request, "price_desc"),
        },
    )


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.order_by("sort_order", "created_at", "pk")

    main_image = images.first()
    canonical_url = request.build_absolute_uri(request.path)
    seo_description = product.description[:160]
    seo_image_url = (
        request.build_absolute_uri(main_image.image.url)
        if main_image
        else ""
    )
    product_schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": seo_description,
        "sku": product.sku,
        "url": canonical_url,
        "offers": {
            "@type": "Offer",
            "availability": "https://schema.org/PreOrder",
            "price": str(product.current_price),
            "priceCurrency": "USD",
            "url": canonical_url,
        },
    }
    if seo_image_url:
        product_schema["image"] = seo_image_url

    product_schema_json = (
        json.dumps(product_schema, ensure_ascii=False)
        .replace("<", "\\u003C")
        .replace(">", "\\u003E")
        .replace("&", "\\u0026")
    )

    return render(
        request,
        "card.html",
        {
            "images": images,
            "main_image": main_image,
            "product": product,
            "canonical_url": canonical_url,
            "product_schema_json": product_schema_json,
            "seo_description": seo_description,
            "seo_image_url": seo_image_url,
        },
    )
