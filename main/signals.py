from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Collection, CollectionImage, ProductImage


FILE_FIELDS = (
    (Collection, "logo_image"),
    (Collection, "main_image"),
    (CollectionImage, "image"),
    (ProductImage, "image"),
)


def _file_name(file_field):
    return getattr(file_field, "name", "") or ""


def _is_file_referenced(name, exclude=None):
    if not name:
        return False

    exclude_model, exclude_pk = exclude or (None, None)

    for model, field_name in FILE_FIELDS:
        queryset = model._default_manager.filter(**{field_name: name})

        if exclude_model is model and exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)

        if queryset.exists():
            return True

    return False


def _delete_file_name_if_unused(name, storage, exclude=None):
    if not name or _is_file_referenced(name, exclude=exclude):
        return

    if storage.exists(name):
        storage.delete(name)


def _delete_file_if_unused(file_field, exclude=None):
    _delete_file_name_if_unused(_file_name(file_field), file_field.storage, exclude=exclude)


def _old_file_names(instance, field_names):
    if not instance.pk:
        return {}

    try:
        old_instance = instance.__class__._default_manager.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return {}

    names = {}
    for field_name in field_names:
        old_name = _file_name(getattr(old_instance, field_name))
        new_name = _file_name(getattr(instance, field_name))

        if old_name and old_name != new_name:
            names[field_name] = old_name

    return names


def _store_old_file_names(instance, field_names):
    instance._old_file_names_for_cleanup = _old_file_names(instance, field_names)


def _delete_replaced_files(instance, old_names):
    for field_name, old_name in old_names.items():
        file_field = getattr(instance, field_name)
        _delete_file_name_if_unused(
            old_name,
            file_field.storage,
            exclude=(instance.__class__, instance.pk),
        )


def _schedule_replaced_files_cleanup(instance):
    old_names = getattr(instance, "_old_file_names_for_cleanup", {}).copy()

    if hasattr(instance, "_old_file_names_for_cleanup"):
        delattr(instance, "_old_file_names_for_cleanup")

    if old_names:
        transaction.on_commit(lambda: _delete_replaced_files(instance, old_names))


@receiver(pre_save, sender=ProductImage)
def store_replaced_product_image(sender, instance, **kwargs):
    _store_old_file_names(instance, ("image",))


@receiver(post_save, sender=ProductImage)
def delete_replaced_product_image(sender, instance, **kwargs):
    _schedule_replaced_files_cleanup(instance)


@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    transaction.on_commit(lambda: _delete_file_if_unused(instance.image))


@receiver(pre_save, sender=Collection)
def store_replaced_collection_images(sender, instance, **kwargs):
    _store_old_file_names(instance, ("logo_image", "main_image"))


@receiver(post_save, sender=Collection)
def delete_replaced_collection_images(sender, instance, **kwargs):
    _schedule_replaced_files_cleanup(instance)


@receiver(post_delete, sender=Collection)
def delete_collection_files(sender, instance, **kwargs):
    transaction.on_commit(lambda: _delete_file_if_unused(instance.logo_image))
    transaction.on_commit(lambda: _delete_file_if_unused(instance.main_image))


@receiver(pre_save, sender=CollectionImage)
def store_replaced_collection_image(sender, instance, **kwargs):
    _store_old_file_names(instance, ("image",))


@receiver(post_save, sender=CollectionImage)
def delete_replaced_collection_image(sender, instance, **kwargs):
    _schedule_replaced_files_cleanup(instance)


@receiver(post_delete, sender=CollectionImage)
def delete_collection_image_file(sender, instance, **kwargs):
    transaction.on_commit(lambda: _delete_file_if_unused(instance.image))
