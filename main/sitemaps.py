from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Collection, Product


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return ("home", "catalog")

    def location(self, item):
        return reverse(item)


class CollectionSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Collection.objects.filter(is_active=True)

    def lastmod(self, collection):
        return collection.updated_at

    def location(self, collection):
        return f"{reverse('catalog')}?collection={collection.slug}"


class ProductSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, product):
        return product.updated_at

    def location(self, product):
        return reverse("product_detail", args=(product.slug,))


sitemaps = {
    "static": StaticViewSitemap,
    "collections": CollectionSitemap,
    "products": ProductSitemap,
}
