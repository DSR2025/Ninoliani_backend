from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html

from .models import (
    Category,
    Collection,
    CollectionImage,
    HomeNewArrival,
    Product,
    ProductImage,
    generate_unique_slug,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ("image_preview",)

    @admin.display(description="Preview")
    def image_preview(self, product_image):
        if product_image.image:
            return format_html(
                '<img src="{}" style="width: 64px; height: 88px; '
                'object-fit: cover; border-radius: 4px;" />',
                product_image.image.url,
            )
        return "—"


class CollectionImageInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        active_count = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            if form.cleaned_data.get("is_active"):
                active_count += 1

        if active_count > 6:
            raise ValidationError(
                "A collection can have a maximum of 6 active gallery images."
            )


class CollectionImageInline(admin.TabularInline):
    model = CollectionImage
    formset = CollectionImageInlineFormSet
    extra = 1
    fields = ("image_preview", "image", "alt_text", "sort_order", "is_active")
    readonly_fields = ("image_preview",)

    @admin.display(description="Preview")
    def image_preview(self, collection_image):
        if collection_image.image:
            return format_html(
                '<img src="{}" style="width: 80px; height: 110px; '
                'object-fit: cover; border-radius: 4px;" />',
                collection_image.image.url,
            )
        return "—"


class ProductAdminForm(forms.ModelForm):
    slug = forms.CharField(
        required=False,
        help_text="Leave empty to generate automatically.",
    )

    class Meta:
        model = Product
        fields = "__all__"

    def clean_slug(self):
        slug = self.cleaned_data.get("slug", "")
        if self.instance.pk and slug == self.instance.slug:
            return slug
        return generate_unique_slug(
            self.instance,
            slug or self.cleaned_data.get("name", ""),
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug", "greek_title")
    inlines = (CollectionImageInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("gallery_images")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        "image_preview",
        "name",
        "sku",
        "slug",
        "color",
        "product_type",
        "price",
        "is_active",
    )
    list_filter = ("is_active", "color", "product_type", "categories", "collection")
    filter_horizontal = ("categories",)
    search_fields = ("name", "sku", "slug", "color", "product_type")
    inlines = (ProductImageInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("images")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "categories":
            kwargs["queryset"] = (
                Category.objects.filter(children__isnull=True)
                .exclude(slug="collections")
                .distinct()
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description="Categories")
    def categories_list(self, product):
        return ", ".join(category.name for category in product.categories.all())

    @admin.display(description="Photo")
    def image_preview(self, product):
        image = product.main_image
        if image:
            return format_html(
                '<img src="{}" style="width: 48px; height: 64px; '
                'object-fit: cover; border-radius: 4px;" />',
                image.image.url,
            )
        return "—"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "sort_order", "created_at")
    list_filter = ("product",)


@admin.register(HomeNewArrival)
class HomeNewArrivalAdmin(admin.ModelAdmin):
    list_display = (
        "image_preview",
        "product",
        "product_sku",
        "product_color",
        "sort_order",
        "is_active",
    )
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = (
        "product__name",
        "product__sku",
        "product__slug",
        "product__color",
        "product__product_type",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product")
            .prefetch_related("product__images")
        )

    @admin.display(description="Photo")
    def image_preview(self, arrival):
        image = arrival.product.main_image
        if image:
            return format_html(
                '<img src="{}" style="width: 48px; height: 64px; '
                'object-fit: cover; border-radius: 4px;" />',
                image.image.url,
            )
        return "—"

    @admin.display(description="SKU", ordering="product__sku")
    def product_sku(self, arrival):
        return arrival.product.sku

    @admin.display(description="Color", ordering="product__color")
    def product_color(self, arrival):
        return arrival.product.color
