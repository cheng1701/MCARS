from django import forms
from .models import Rank, Theme, RankImage, Genre, Branch, RankSettings
from rank.models import MemberRank, ChildRank
import datetime


class RankForm(forms.ModelForm):
    class Meta:
        model = Rank
        fields = ['paygrade', 'short_name', 'long_name']
        widgets = {
            'paygrade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., E-1, O-3'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'long_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ThemeForm(forms.ModelForm):
    class Meta:
        model = Theme
        fields = ['name', 'description', 'genre', 'branch', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'genre': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RankImageForm(forms.ModelForm):
    class Meta:
        model = RankImage
        fields = ['rank', 'image']
        widgets = {
            'rank': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'abbreviation', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'abbreviation': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class RankSettingsForm(forms.ModelForm):
    class Meta:
        model = RankSettings
        fields = ['default_paygrade', 'default_theme']
        widgets = {
            'default_paygrade': forms.Select(attrs={'class': 'form-select'}),
            'default_theme': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show all available themes
        self.fields['default_theme'].queryset = Theme.objects.all()


class MemberRankForm(forms.ModelForm):
    class Meta:
        model = MemberRank
        fields = ['rank', 'preferred_theme', 'effective_date', 'notes']
        widgets = {
            'rank': forms.Select(attrs={'class': 'form-select'}),
            'preferred_theme': forms.Select(attrs={'class': 'form-select'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['effective_date'].initial = datetime.date.today()

        # Only show active themes
        self.fields['preferred_theme'].queryset = Theme.objects.filter(is_active=True)
        self.fields['preferred_theme'].required = False
        self.fields['preferred_theme'].help_text = "The theme that will be used to display this member's rank insignia"


class ChildRankForm(forms.ModelForm):
    class Meta:
        model = ChildRank
        fields = ['rank', 'preferred_theme', 'effective_date', 'notes']
        widgets = {
            'rank': forms.Select(attrs={'class': 'form-select'}),
            'preferred_theme': forms.Select(attrs={'class': 'form-select'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes about this rank assignment...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['effective_date'].initial = datetime.date.today()

        # Make theme and notes optional
        self.fields['preferred_theme'].required = False
        self.fields['notes'].required = False

        # Add empty option for theme
        self.fields['preferred_theme'].empty_label = "Use Default Theme"
        self.fields['preferred_theme'].queryset = Theme.objects.filter(is_active=True)
        self.fields['preferred_theme'].help_text = "The theme that will be used to display this child's rank insignia"
