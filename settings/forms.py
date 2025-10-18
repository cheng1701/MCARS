from django import forms
from django.contrib.auth.models import Group, User

from Members.models import Member


class MemberSelectForm(forms.Form):
    member = forms.ModelChoiceField(queryset=Member.objects.select_related('user').all(), required=True, label='Select Member')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].widget.attrs.update({'class': 'form-select'})


class MemberRolesForm(forms.Form):
    is_staff = forms.BooleanField(required=False, label='Staff (can access admin-level features)')
    is_superuser = forms.BooleanField(required=False, label='Superuser (full permissions)')
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Groups'
    )

    def __init__(self, *args, **kwargs):
        self.user: User = kwargs.pop('user_instance')
        super().__init__(*args, **kwargs)
        # Initial flags
        self.fields['is_staff'].initial = self.user.is_staff
        self.fields['is_superuser'].initial = self.user.is_superuser
        # Initial groups
        self.fields['groups'].initial = self.user.groups.all()

    def save(self):
        # Update flags
        self.user.is_staff = self.cleaned_data.get('is_staff', False)
        self.user.is_superuser = self.cleaned_data.get('is_superuser', False)
        self.user.save()
        # Update groups to match selection exactly
        selected_groups = list(self.cleaned_data.get('groups') or [])
        self.user.groups.set(selected_groups)
        return self.user
