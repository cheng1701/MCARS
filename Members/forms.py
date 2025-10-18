from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Member, MembershipType, Address, Child, FAQ, FAQCategory
from .utils import is_email_blocked

# --------------------
# Core Member forms
# --------------------
class MemberRegistrationForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['membership_type', 'phone_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership_type'].queryset = MembershipType.objects.all()
        self.fields['membership_type'].empty_label = None
        self.fields['membership_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Phone Number'})


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['street', 'city', 'state', 'zip_code', 'country']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            widget = self.fields[field].widget
            if isinstance(widget, forms.Select):
                widget.attrs.update({'class': 'form-select'})
            else:
                widget.attrs.update({'class': 'form-control'})


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['first_name', 'last_name', 'birthdate', 'notes']
        widgets = {
            'birthdate': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class ThemePreferenceForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['theme_preference']
        widgets = {
            'theme_preference': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Normalize CSS consistently
        for field in self.fields:
            widget = self.fields[field].widget
            if isinstance(widget, forms.Select):
                widget.attrs.update({'class': 'form-select'})
            else:
                widget.attrs.update({'class': 'form-control'})


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


# --------------------
# FAQ management forms
# --------------------
class FAQCategoryForm(forms.ModelForm):
    class Meta:
        model = FAQCategory
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['category', 'question', 'answer', 'order', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'question': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set sensible defaults for new records
        if not self.instance.pk:
            self.fields['order'].initial = self.fields['order'].initial or 0
            if 'is_active' not in self.initial:
                self.fields['is_active'].initial = True


# --------------------
# Auth and contact forms
# --------------------
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            widget = self.fields[field].widget
            if isinstance(widget, (forms.Select,)):
                widget.attrs.update({'class': 'form-select'})
            else:
                widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if is_email_blocked(email):
            raise ValidationError("This email address cannot be used.")
        return email


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}))
    subject = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Your Message'}), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Widgets already have classes above for these fields; keep consistency
        pass

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if is_email_blocked(email):
            raise ValidationError("This email address cannot be used.")
        return email


# --------------------
# Manager tool: convert child to member
# --------------------
class ConvertChildToMemberForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    membership_type = forms.ModelChoiceField(queryset=MembershipType.objects.all(), required=True)
    approve_now = forms.BooleanField(required=False, initial=False, help_text="Approve membership immediately")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            widget = self.fields[field].widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(widget, (forms.Select,)):
                widget.attrs.update({'class': 'form-select'})
            else:
                widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if is_email_blocked(email):
            raise ValidationError('This email address cannot be used.')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email
