from django.core.management.base import BaseCommand
from django.db.models import Q

from main.models import Category


class Command(BaseCommand):
    help = "Create the default catalog categories without duplicating existing entries."

    def handle(self, *args, **options):
        root_categories = (
            ("New Arrivals", "new-arrivals"),
            ("Dresses", "dresses"),
            ("Tops", "tops"),
            ("Pants", "pants"),
            ("Skirts", "skirts"),
            ("Bridal", "bridal"),
            ("Collections", "collections"),
        )
        dress_categories = (
            ("Mini Dresses", "mini-dresses"),
            ("Maxi Dresses", "maxi-dresses"),
            ("Midi Dresses", "midi-dresses"),
        )

        created_count = 0
        skipped_count = 0

        dresses = None

        for name, slug in root_categories:
            category, created = self._get_or_create_category(name, slug)
            if slug == "dresses":
                dresses = category
            created_count, skipped_count = self._report_result(
                name,
                created,
                created_count,
                skipped_count,
            )

        for name, slug in dress_categories:
            _, created = self._get_or_create_category(name, slug, parent=dresses)
            created_count, skipped_count = self._report_result(
                name,
                created,
                created_count,
                skipped_count,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Categories ready: {created_count} created, {skipped_count} skipped."
            )
        )

    def _get_or_create_category(self, name, slug, parent=None):
        category = Category.objects.filter(Q(name=name) | Q(slug=slug)).first()
        if category:
            return category, False

        return Category.objects.create(name=name, slug=slug, parent=parent), True

    def _report_result(self, name, created, created_count, skipped_count):
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created: {name}"))
            return created_count + 1, skipped_count

        self.stdout.write(f"Skipped: {name}")
        return created_count, skipped_count + 1
