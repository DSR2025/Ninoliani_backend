from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def price_display(value):
    if value is None:
        return ""

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return value

    if amount == amount.to_integral_value():
        return str(amount.quantize(Decimal("1")))

    return format(amount, "f")
