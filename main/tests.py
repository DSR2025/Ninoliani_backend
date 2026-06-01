from django.contrib.staticfiles import finders
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_HOST_USER="sender@example.com",
    CONTACT_EMAIL_TO="contact@example.com",
)
class ContactViewTests(TestCase):
    def setUp(self):
        self.url = reverse("contact")
        self.valid_data = {
            "fullName": "Test User",
            "phone": "+1 555 123 4567",
            "email": "test@example.com",
            "comment": "Please contact me.",
            "consent": "on",
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
