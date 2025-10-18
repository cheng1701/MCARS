from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid
import os
from .validators import validate_image_extension, validate_image_size

# Create your models here.
class MembershipType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.IntegerField(help_text="0 for lifetime")
    is_family = models.BooleanField(default=False)
    billing_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
            ('lifetime', 'Lifetime'),
            ('free', 'Free')
        ],
        default='monthly'
    )

    def __str__(self):
        return self.name

class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"

class Member(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
        ('blocked', 'Blocked'),
        ('blocked', 'Blocked'),
    ]

    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    membership_type = models.ForeignKey(MembershipType, on_delete=models.SET_NULL, null=True)
    phone_number = models.CharField(max_length=20)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    member_since = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    membership_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    approval_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_members')
    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='dark')
    profile_image = models.ImageField(
        upload_to='profile_images/', 
        null=True, 
        blank=True,
        validators=[validate_image_extension, validate_image_size],
        help_text='Upload a profile image (JPG, PNG, or GIF, max 5MB)'
    )

    def __str__(self):
        return self.get_full_name_with_rank()

    def get_rank(self):
        """Get the member's assigned rank or default rank if none is assigned"""
        try:
            return self.rank_association.rank
        except:
            # If no rank is assigned, use the default rank from settings
            from rank.models import RankSettings
            settings = RankSettings.objects.first()
            if settings and settings.default_paygrade:
                return settings.default_paygrade
            return None

    def get_rank_image(self):
        """Get the rank image URL for the member based on their rank and the default theme"""
        from rank.models import RankSettings, RankImage

        # Get the member's rank (either assigned or default)
        rank = self.get_rank()
        if not rank:
            return None

        # Get the default theme from settings
        settings = RankSettings.get_settings()
        theme = settings.default_theme
        if not theme:
            return None

        # Try to get the rank image for this rank and theme
        try:
            rank_image = RankImage.objects.get(rank=rank, theme=theme)
            return rank_image.image.url
        except RankImage.DoesNotExist:
            return None

    def get_full_name(self):
        """Get the member's full name without rank"""
        # Use the ranked name by default
        return self.get_ranked_name()

    def get_ranked_name(self):
        """Return member name with rank prefix"""
        try:
            # Try to get member's assigned rank
            rank = self.rank_association.rank.short_name
        except:
            # If no rank assigned, use default from settings
            from rank.models import RankSettings
            settings = RankSettings.get_settings()
            rank = settings.default_paygrade.short_name if settings and settings.default_paygrade else ''

        if rank:
            return f"{rank} {self.user.first_name} {self.user.last_name}"
        else:
            return f"{self.user.first_name} {self.user.last_name}"

    def get_full_name_with_rank(self):
        """Get the member's full name with rank prefix"""
        rank = self.get_rank()
        if rank:
            return f"{rank.short_name} {self.user.first_name} {self.user.last_name}"
        return self.get_full_name()

    def set_expiration_date(self):
        if self.membership_type.billing_frequency == 'lifetime':
            self.expiration_date = None
        elif self.membership_type.billing_frequency == 'free':
            self.expiration_date = timezone.now() + timedelta(days=365)  # 1 year free
        elif self.membership_type.billing_frequency == 'monthly':
            self.expiration_date = timezone.now() + timedelta(days=30)  # 30 days
        elif self.membership_type.billing_frequency == 'yearly':
            self.expiration_date = timezone.now() + timedelta(days=365)  # 1 year
        self.save()

    def is_active(self):
        if self.status != 'active':
            return False
        if self.membership_type.billing_frequency == 'lifetime':
            return True
        if not self.expiration_date:
            return False
        return timezone.now() < self.expiration_date

    def approve(self, approver):
        self.status = 'active'
        self.approval_date = timezone.now()
        self.approved_by = approver
        self.set_expiration_date()
        self.save()

        # Assign default rank from settings
        # Import here to avoid circular imports
        from rank.models import RankSettings, MemberRank

        # Check if member already has a rank assignment
        try:
            # This will raise MemberRank.DoesNotExist if no rank exists
            self.rank_association
            has_rank = True
        except:
            has_rank = False

        # Only assign default rank if member doesn't already have one
        if not has_rank:
            settings = RankSettings.objects.first()
            if settings and settings.default_paygrade:
                MemberRank.objects.create(
                    member=self,
                    rank=settings.default_paygrade,
                    assigned_by=approver,
                    notes="Automatically assigned default rank upon membership approval."
                )

        # Import here to avoid circular import
        from .utils import send_approval_email
        send_approval_email(self)

    def reject(self):
        self.status = 'rejected'
        self.save()

class Child(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    parent = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='children')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birthdate = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    profile_image = models.ImageField(
        upload_to='child_profile_images/', 
        null=True, 
        blank=True,
        validators=[validate_image_extension, validate_image_size],
        help_text='Upload a profile image (JPG, PNG, or GIF, max 5MB)'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    child_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        """Get the child's full name"""
        return f"{self.first_name} {self.last_name}"

    def get_ranked_name(self):
        """Return child name with rank prefix"""
        try:
            # Try to get child's assigned rank
            rank = self.child_rank_association.rank.short_name
            return f"{rank} {self.first_name} {self.last_name}"
        except:
            # If no rank assigned, return name without rank
            return self.get_full_name()

    def get_rank(self):
        """Get the child's assigned rank or default rank if none is assigned"""
        try:
            return self.child_rank_association.rank
        except:
            # If no rank is assigned, use the default rank from settings
            from rank.models import RankSettings
            settings = RankSettings.objects.first()
            if settings and settings.default_paygrade:
                return settings.default_paygrade
            return None

    def get_rank_image(self):
        """Get the rank image URL for the child based on their rank and the default theme"""
        from rank.models import RankSettings, RankImage

        # Get the child's rank (either assigned or default)
        rank = self.get_rank()
        if not rank:
            return None

        # Get the default theme from settings
        settings = RankSettings.get_settings()
        theme = settings.default_theme
        if not theme:
            return None

        # Try to get the rank image for this rank and theme
        try:
            rank_image = RankImage.objects.get(rank=rank, theme=theme)
            return rank_image.image.url
        except RankImage.DoesNotExist:
            return None

    class Meta:
        verbose_name_plural = "Children"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Payment of ${self.amount} by {self.member} on {self.payment_date.strftime('%Y-%m-%d')}"

class FAQCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of display")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "FAQ Category"
        verbose_name_plural = "FAQ Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class FAQ(models.Model):
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text="Order of display within category")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_faqs')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_faqs')

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['category__order', 'category', 'order', '-updated_at']

    def __str__(self):
        return self.question
