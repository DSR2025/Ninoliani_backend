from django import forms


class ContactForm(forms.Form):
    fullName = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=30)
    email = forms.EmailField(max_length=254)
    comment = forms.CharField(max_length=1000, required=False)
    consent = forms.BooleanField()
