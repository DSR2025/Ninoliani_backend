from django import forms
from django.core.validators import RegexValidator


phone_validator = RegexValidator(
    regex=r"^[0-9+\-\s()]{6,30}$",
    message="Enter a valid phone number.",
)


class ContactForm(forms.Form):
    fullName = forms.CharField(min_length=2, max_length=100)
    phone = forms.CharField(max_length=30, validators=[phone_validator])
    email = forms.EmailField(max_length=254)
    comment = forms.CharField(max_length=1000, required=False)
    consent = forms.BooleanField()

    def clean_fullName(self):
        full_name = self.cleaned_data["fullName"].strip()

        if not any(character.isalpha() for character in full_name):
            raise forms.ValidationError("Enter a valid name.")

        return full_name
