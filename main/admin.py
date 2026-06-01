from django.contrib import admin

from .models import Category, Collection, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "categories_list",
        "collection",
        "price",
        "discount_price",
        "is_active",
    )
    list_filter = ("is_active", "categories", "collection", "color", "product_type")
    filter_horizontal = ("categories",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "sku")
    inlines = (ProductImageInline,)

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


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "sort_order", "created_at")
    list_filter = ("product",)
