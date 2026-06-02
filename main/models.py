import uuid

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def generate_unique_slug(instance, value):
    slug = slugify(value, allow_unicode=True) or uuid.uuid4().hex[:8]
    unique_slug = slug
    counter = 2

    while instance.__class__.objects.filter(slug=unique_slug).exclude(pk=instance.pk).exists():
        unique_slug = f"{slug}-{counter}"
        counter += 1

    return unique_slug


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, allow_unicode=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="children",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Collection(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, allow_unicode=True)
    greek_title = models.CharField(max_length=255, blank=True)
    logo_image = models.ImageField(
        upload_to="collections/logos/",
        blank=True,
        null=True,
    )
    main_image = models.ImageField(
        upload_to="collections/images/",
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "name")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, allow_unicode=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    sku = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    description = models.TextField()
    materials = models.TextField()
    categories = models.ManyToManyField(
        Category,
        related_name="products",
        blank=True,
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        related_name="products",
        blank=True,
        null=True,
    )
    color = models.CharField(max_length=100)
    product_type = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.pk or not self.slug:
            self.slug = generate_unique_slug(self, self.slug or self.name)
        if not self.sku:
            self.sku = f"NIN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        return self.discount_price if self.discount_price is not None else self.price

    @property
    def main_image(self):
        return self.images.first()

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return " — ".join(
            part
            for part in (self.name, self.color, self.product_type, self.sku)
            if part
        )


class HomeNewArrival(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="home_new_arrivals",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("sort_order", "pk")
        verbose_name = "Homepage New Arrival"
        verbose_name_plural = "Homepage New Arrivals"

    def __str__(self):
        return str(self.product)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sort_order", "created_at", "pk")

    def __str__(self):
        return f"{self.product.name} image"
