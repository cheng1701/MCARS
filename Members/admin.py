from django.contrib import admin
from .models import MembershipType, Address, Member, Child, Payment
from .utils import block_email

class ChildInline(admin.TabularInline):
    model = Child
    extra = 0

class MemberAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'membership_id', 'status', 'membership_type', 'member_since', 'expiration_date')
    list_filter = ('status', 'membership_type')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone_number', 'membership_id')
    inlines = [ChildInline]
    actions = ['block_email_address']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'

    def block_email_address(self, request, queryset):
        for member in queryset:
            block_email(member.user.email)
            member.status = 'blocked'
            member.save()

        self.message_user(request, f"Blocked {queryset.count()} email addresses")
    block_email_address.short_description = "Block selected members' email addresses"

class MembershipTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_months', 'is_family', 'billing_frequency')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'payment_date', 'status')
    list_filter = ('status', 'payment_date')
    search_fields = ('member__user__first_name', 'member__user__last_name', 'transaction_id')

# Register all models - each one only once
admin.site.register(MembershipType, MembershipTypeAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Address)
admin.site.register(Child)
admin.site.register(Payment, PaymentAdmin)
