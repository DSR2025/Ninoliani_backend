from django.contrib import admin
from django.contrib.staticfiles import finders
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from .admin import (
    HomeNewArrivalAdmin,
    ProductAdmin,
    ProductAdminForm,
    ProductImageInline,
)
from .models import HomeNewArrival, Product, ProductImage
from .views import verify_turnstile_token


class HomeNewArrivalTests(TestCase):
    def create_product(self, name, price="100.00"):
        return Product.objects.create(
            name=name,
            price=price,
            description="Description",
            materials="Materials",
            color="Black",
            product_type="Dress",
        )

    def test_homepage_shows_at_most_three_active_arrivals_in_sort_order(self):
        products = [
            self.create_product(name)
            for name in ("Fourth", "Second", "First", "Third")
        ]
        arrivals = [
            HomeNewArrival.objects.create(product=product, sort_order=sort_order)
            for sort_order, product in zip((40, 20, 10, 30), products)
        ]

        response = self.client.get(reverse("home"))

        homepage_arrivals = list(response.context["new_arrivals"])
        self.assertEqual(
            [arrival.product.name for arrival in homepage_arrivals],
            ["First", "Second", "Third"],
        )

        arrivals[0].sort_order = 5
        arrivals[0].save(update_fields=("sort_order",))

        response = self.client.get(reverse("home"))

        homepage_arrivals = list(response.context["new_arrivals"])
        self.assertEqual(
            [arrival.product.name for arrival in homepage_arrivals],
            ["Fourth", "First", "Second"],
        )

    def test_disabled_arrival_is_not_shown(self):
        product = self.create_product("Hidden")
        HomeNewArrival.objects.create(product=product, is_active=False)

        response = self.client.get(reverse("home"))

        self.assertNotContains(response, product.name)

    def test_inactive_product_is_not_shown(self):
        product = self.create_product("Inactive")
        product.is_active = False
        product.save(update_fields=("is_active",))
        HomeNewArrival.objects.create(product=product)

        response = self.client.get(reverse("home"))

        self.assertNotContains(response, product.name)

    def test_homepage_flip_card_links_to_product_and_uses_second_image_on_back(self):
        product = self.create_product("Featured")
        product.discount_price = "75.00"
        product.save(update_fields=("discount_price",))
        ProductImage.objects.create(
            product=product,
            image="products/featured-main.webp",
            sort_order=1,
        )
        ProductImage.objects.create(
            product=product,
            image="products/featured-hover.webp",
            sort_order=2,
        )
        HomeNewArrival.objects.create(product=product)

        response = self.client.get(reverse("home"))

        self.assertContains(response, product.get_absolute_url())
        self.assertContains(response, "products/featured-main.webp")
        self.assertContains(response, "products/featured-hover.webp")
        self.assertContains(response, 'aria-label="View Featured"')
        self.assertContains(response, "hero_new_arrival_flip_back")
        self.assertContains(response, "Description")
        self.assertNotContains(response, "VIEW PRODUCT")
        self.assertContains(response, "$75.00")
        self.assertNotContains(response, "$100.00")

    def test_homepage_flip_card_uses_first_image_as_back_fallback(self):
        product = self.create_product("One image")
        ProductImage.objects.create(product=product, image="products/one-image.webp")
        HomeNewArrival.objects.create(product=product)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "products/one-image.webp", count=2)

    def test_homepage_flip_card_uses_description_fallback(self):
        product = self.create_product("Fallback")
        product.description = ""
        product.save(update_fields=("description",))
        ProductImage.objects.create(product=product, image="products/fallback.webp")
        HomeNewArrival.objects.create(product=product)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Discover the piece.")

    def test_homepage_does_not_break_when_arrival_has_no_image(self):
        product = self.create_product("Without image")
        HomeNewArrival.objects.create(product=product)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'aria-label="View Without image"')


class ProductAdminTests(TestCase):
    def create_product(self, name="Hydra Dress", slug="hydra-dress", color="White"):
        return Product.objects.create(
            name=name,
            slug=slug,
            price="100.00",
            description="Description",
            materials="Materials",
            color=color,
            product_type="Mini Dress",
        )

    def test_products_with_same_name_get_unique_slugs_skus_and_urls(self):
        first_product = self.create_product()
        second_product = self.create_product(color="Blue")

        self.assertEqual(first_product.slug, "hydra-dress")
        self.assertEqual(second_product.slug, "hydra-dress-2")
        self.assertNotEqual(first_product.sku, second_product.sku)
        self.assertNotEqual(
            first_product.get_absolute_url(),
            second_product.get_absolute_url(),
        )
        self.assertEqual(self.client.get(first_product.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(second_product.get_absolute_url()).status_code, 200)

    def test_products_with_same_name_and_empty_slug_get_incremented_slugs(self):
        products = [
            self.create_product(slug="", color=color)
            for color in ("White", "Blue", "Black")
        ]

        self.assertEqual(
            [product.slug for product in products],
            ["hydra-dress", "hydra-dress-2", "hydra-dress-3"],
        )

    def test_existing_product_slug_is_preserved_when_saved_again(self):
        product = self.create_product()
        product.name = "Renamed Dress"

        product.save()

        self.assertEqual(product.slug, "hydra-dress")

    def test_product_admin_form_normalizes_conflicting_manual_slug(self):
        self.create_product()
        form = ProductAdminForm(
            data={
                "name": "Hydra Dress",
                "slug": "Hydra Dress",
                "price": "100.00",
                "description": "Description",
                "materials": "Materials",
                "color": "Blue",
                "product_type": "Mini Dress",
                "is_active": "on",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().slug, "hydra-dress-2")

    def test_product_string_identifies_variant(self):
        product = self.create_product()

        self.assertEqual(
            str(product),
            f"Hydra Dress — White — Mini Dress — {product.sku}",
        )

    def test_product_and_home_arrival_admin_preview_first_sorted_image(self):
        product = self.create_product()
        ProductImage.objects.create(
            product=product,
            image="products/second.webp",
            sort_order=20,
        )
        ProductImage.objects.create(
            product=product,
            image="products/first.webp",
            sort_order=10,
        )
        arrival = HomeNewArrival.objects.create(product=product)

        product_preview = ProductAdmin(Product, admin.site).image_preview(product)
        arrival_preview = HomeNewArrivalAdmin(
            HomeNewArrival,
            admin.site,
        ).image_preview(arrival)

        self.assertIn("products/first.webp", product_preview)
        self.assertNotIn("products/second.webp", product_preview)
        self.assertIn("products/first.webp", arrival_preview)

    def test_product_image_inline_preview_handles_image_and_empty_object(self):
        product = self.create_product()
        product_image = ProductImage.objects.create(
            product=product,
            image="products/inline.webp",
        )
        inline = ProductImageInline(Product, admin.site)

        self.assertIn("products/inline.webp", inline.image_preview(product_image))
        self.assertEqual(inline.image_preview(ProductImage()), "—")

    def test_sitemap_contains_both_products_with_same_name(self):
        first_product = self.create_product()
        second_product = self.create_product(color="Blue")

        response = self.client.get(reverse("django.contrib.sitemaps.views.sitemap"))

        self.assertContains(response, first_product.get_absolute_url())
        self.assertContains(response, second_product.get_absolute_url())


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_HOST_USER="sender@example.com",
    CONTACT_EMAIL_TO="contact@example.com",
    TURNSTILE_SITE_KEY="test-site-key",
    TURNSTILE_SECRET_KEY="test-secret-key",
)
class ContactViewTests(TestCase):
    def setUp(self):
        self.url = reverse("contact")
        self.turnstile_patcher = patch(
            "main.views.verify_turnstile_token",
            return_value=True,
        )
        self.mocked_turnstile = self.turnstile_patcher.start()
        self.addCleanup(self.turnstile_patcher.stop)
        self.valid_data = {
            "fullName": "Test User",
            "phone": "+1 555 123 4567",
            "email": "test@example.com",
            "comment": "Please contact me.",
            "consent": "on",
            "cf-turnstile-response": "valid-token",
        }

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_valid_submission_sends_plain_text_email(self):
        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "ok": True,
                "message": "Message sent successfully",
            },
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "New contact request from Ninoliani")
        self.assertEqual(mail.outbox[0].to, ["contact@example.com"])
        self.assertIn("Name: Test User", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].alternatives, [])

    def test_invalid_submission_returns_field_errors(self):
        response = self.client.post(
            self.url,
            {
                "fullName": "",
                "phone": "x" * 31,
                "email": "not-an-email",
                "comment": "x" * 1001,
            },
        )

        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertIn("fullName", errors)
        self.assertIn("phone", errors)
        self.assertIn("email", errors)
        self.assertIn("comment", errors)
        self.assertIn("consent", errors)
        self.assertEqual(mail.outbox, [])

    def test_missing_captcha_token_is_rejected(self):
        self.mocked_turnstile.return_value = False
        data = {**self.valid_data}
        data.pop("cf-turnstile-response")

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["errors"]["captcha"],
            "Please complete the captcha.",
        )
        self.assertEqual(mail.outbox, [])

    def test_invalid_captcha_token_is_rejected(self):
        self.mocked_turnstile.return_value = False
        data = {**self.valid_data, "cf-turnstile-response": "invalid-token"}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("captcha", response.json()["errors"])
        self.assertEqual(mail.outbox, [])

    @override_settings(DEBUG=True, TURNSTILE_SECRET_KEY="")
    def test_turnstile_can_be_bypassed_locally_when_not_configured(self):
        self.assertTrue(verify_turnstile_token(""))

    @override_settings(DEBUG=False, TURNSTILE_SECRET_KEY="")
    def test_turnstile_cannot_be_bypassed_in_production(self):
        self.assertFalse(verify_turnstile_token(""))

    def test_phone_with_letters_is_rejected(self):
        data = {**self.valid_data, "phone": "qwerty123abc"}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("phone", response.json()["errors"])
        self.assertEqual(mail.outbox, [])

    def test_invalid_email_is_rejected(self):
        data = {**self.valid_data, "email": "test@"}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])
        self.assertEqual(mail.outbox, [])

    def test_name_without_letters_is_rejected(self):
        data = {**self.valid_data, "fullName": "123456"}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("fullName", response.json()["errors"])
        self.assertEqual(mail.outbox, [])

    @patch("main.views.send_mail", side_effect=RuntimeError("SMTP unavailable"))
    def test_email_failure_returns_safe_json_error(self, mocked_send_mail):
        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(
            response.content,
            {
                "ok": False,
                "error": "Email sending failed",
            },
        )
        mocked_send_mail.assert_called_once()

    @patch("main.views.send_mail", return_value=0)
    def test_unsent_email_returns_safe_json_error(self, mocked_send_mail):
        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(
            response.content,
            {
                "ok": False,
                "error": "Email sending failed",
            },
        )
        mocked_send_mail.assert_called_once()

    def test_csrf_token_is_required(self):
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 403)

    def test_obsolete_php_files_are_not_static_assets(self):
        self.assertIsNone(finders.find("send.php"))
        self.assertIsNone(finders.find("test.php"))
        self.assertIsNone(finders.find("vendor/autoload.php"))

    def test_favicon_is_a_static_asset(self):
        self.assertIsNotNone(finders.find("img/favicon.svg"))
