import os
import os
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Q, Prefetch
from datetime import timedelta
import uuid

from django.core.paginator import Paginator

from .forms import CustomUserCreationForm, MemberRegistrationForm, AddressForm, ChildForm, ProfileForm, ThemePreferenceForm, ContactForm, FAQCategoryForm, FAQForm, ConvertChildToMemberForm
from django import forms
from .models import Member, MembershipType, Address, Child, Payment, FAQCategory, FAQ
from .utils import is_email_blocked, increment_failed_attempts, block_email, send_registration_email, reset_failed_attempts

# Helper functions
def is_member_manager(user):
    return user.groups.filter(name__in=['Rank Manager', 'rank_manager']).exists() or user.is_staff

# Public views

def home(request):
    # If a user is already authenticated, make the dashboard the first page they see
    if request.user.is_authenticated:
        return redirect('members:member_dashboard')
    return render(request, 'members/home.html')

def about(request):
    return render(request, 'members/about.html')

def membership_plans(request):
    membership_types = MembershipType.objects.all()
    return render(request, 'members/membership_plans.html', {
        'membership_types': membership_types,
        'page_title': 'Membership Plans'
    })

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Extract form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Prepare email content
            email_subject = f"Contact Form: {subject}"
            email_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            from_email = email
            recipient_list = ['admin@yourorganization.com']  # Change this to your email address

            # Send email
            from django.core.mail import send_mail
            try:
                send_mail(email_subject, email_message, from_email, recipient_list)
                messages.success(request, "Your message has been sent. We'll get back to you soon!")
                return redirect('members:contact')  # Redirect to fresh form
            except Exception as e:
                messages.error(request, f"There was an error sending your message. Please try again later.")
    else:
        form = ContactForm()

    return render(request, 'members/contact.html', {'form': form})

def faq(request):
    membership_types = MembershipType.objects.all()
    faq_categories = FAQCategory.objects.prefetch_related(
        Prefetch('faqs', queryset=FAQ.objects.filter(is_active=True))
    ).all()

    # Ensure all categories have slugs
    for category in faq_categories:
        if not category.slug:
            from django.utils.text import slugify
            category.slug = slugify(category.name)
            category.save()

    return render(request, 'members/faq.html', {
        'membership_types': membership_types,
        'faq_categories': faq_categories
    })

# Registration and authentication
def register(request):
    # Pre-select membership type if plan parameter is provided
    selected_plan = request.GET.get('plan')
    initial_data = {}

    if selected_plan:
        try:
            membership_type = MembershipType.objects.get(id=selected_plan)
            initial_data = {'membership_type': membership_type}
        except MembershipType.DoesNotExist:
            pass

    if request.method == 'POST':
        # Get IP address
        ip_address = request.META.get('REMOTE_ADDR')

        # Check if email is blocked
        email = request.POST.get('email')

        if is_email_blocked(email):
            messages.error(request, "Registration failed. This email address cannot be used.")
            increment_failed_attempts(ip_address)
            return redirect('members:register')

        user_form = CustomUserCreationForm(request.POST)
        member_form = MemberRegistrationForm(request.POST)
        address_form = AddressForm(request.POST)

        if user_form.is_valid() and member_form.is_valid() and address_form.is_valid():
            # Create user
            user = user_form.save()

            # Create address
            address = address_form.save()

            # Create member
            member = member_form.save(commit=False)
            member.user = user
            member.address = address
            member.status = 'pending'
            member.membership_id = str(uuid.uuid4())[:8].upper()
            member.save()

            # Create initial payment record if not free tier
            if member.membership_type.billing_frequency != 'free':
                payment = Payment.objects.create(
                    member=member,
                    amount=member.membership_type.price,
                    status='pending',
                    payment_method='Registration payment'
                )

            # Send registration email
            send_registration_email(member)

            # Reset failed attempts for this IP
            ip_address = request.META.get('REMOTE_ADDR')
            reset_failed_attempts(ip_address)

            return redirect('members:registration_success')
    else:
        user_form = CustomUserCreationForm()
        member_form = MemberRegistrationForm(initial=initial_data)
        address_form = AddressForm()

    return render(request, 'members/register.html', {
        'user_form': user_form,
        'member_form': member_form,
        'address_form': address_form,
        'membership_types': MembershipType.objects.all()
    })

def registration_success(request):
    return render(request, 'members/registration_success.html')

def logout_redirect(request):
    """
    Logs out the user and redirects to the home page
    """
    # Log out the user
    logout(request)

    # Redirect to home page
    return redirect('members:home')

def logout_user(request):
    """
    Handles user logout and redirects to home
    """
    # Log out the user
    logout(request)

    # Add a success message
    messages.success(request, "You have been successfully logged out.")

    # Redirect to home page
    return redirect('members:home')

@login_required
def toggle_theme(request):
    from django.http import JsonResponse
    import json

    if request.method == 'POST' and request.user.is_authenticated:
        try:
            # Get the current user's member profile
            member = request.user.member

            # Toggle between 'light' and 'dark' theme
            if member.theme_preference == 'light':
                member.theme_preference = 'dark'
            else:
                member.theme_preference = 'light'

            # Save the updated preference
            member.save()

            # Return success response
            return JsonResponse({'success': True, 'theme': member.theme_preference})

        except Exception as e:
            # Return error response if something went wrong
            return JsonResponse({'success': False, 'error': str(e)})

    # Return error for non-POST requests or unauthenticated users
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    """
    Toggle between light and dark theme preference for the user
    """
    if request.method == 'POST':
        try:
            member = request.user.member
            # Toggle theme preference
            if member.theme_preference == 'light':
                member.theme_preference = 'dark'
            else:
                member.theme_preference = 'light'
            member.save()
            return JsonResponse({'success': True, 'theme': member.theme_preference})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
# Member portal views
@login_required
def member_dashboard(request):
    from .models import Member, Address, MembershipType, Child, Payment

    try:
        member = request.user.member
    except Member.DoesNotExist:
        # Create a default address
        address = Address.objects.create(
            street='',
            city='',
            state='',
            zip_code='',
            country='USA'
        )

        # Get the default/free membership type
        try:
            membership_type = MembershipType.objects.filter(billing_frequency='free').first()
            if not membership_type:
                membership_type = MembershipType.objects.first()
        except:
            membership_type = None

        # Create a new member profile
        member = Member.objects.create(
            user=request.user,
            phone_number='',
            address=address,
            status='pending',
            membership_type=membership_type,
            membership_id=str(uuid.uuid4())[:8].upper()
        )

        # Redirect to edit profile immediately
        messages.info(request, "Welcome! Please complete your profile information to activate your membership.")
        return redirect('members:edit_profile')

    # Check if profile is incomplete
    profile_incomplete = False

    # Check required fields
    if not member.phone_number or member.phone_number.strip() == '':
        profile_incomplete = True

    # Check if address is missing or incomplete
    if not member.address or not all([
        member.address.street, 
        member.address.city, 
        member.address.state, 
        member.address.zip_code
    ]):
        profile_incomplete = True

    # Check if user profile is incomplete
    if not all([
        member.user.first_name,
        member.user.last_name,
        member.user.email
    ]):
        profile_incomplete = True

    if profile_incomplete:
        messages.info(request, "Please complete your profile information to ensure you have full access to all member features.")
        return redirect('members:edit_profile')

    children = Child.objects.filter(parent=member)
    recent_payments = Payment.objects.filter(member=member).order_by('-payment_date')[:5]

    return render(request, 'members/dashboard.html', {
        'member': member,
        'children': children,
        'recent_payments': recent_payments
    })

@login_required
def member_profile(request):
    # Get or create a member profile for the logged in user
    from .models import Member, Address, MembershipType

    try:
        member = request.user.member
    except Member.DoesNotExist:
        # Create a default address
        address = Address.objects.create(
            street='',
            city='',
            state='',
            zip_code='',
            country='USA'
        )

        # Get the default/free membership type
        try:
            membership_type = MembershipType.objects.filter(billing_frequency='free').first()
            if not membership_type:
                membership_type = MembershipType.objects.first()
        except:
            membership_type = None

        # Create a new member profile
        member = Member.objects.create(
            user=request.user,
            phone_number='',
            address=address,
            status='pending',
            membership_type=membership_type,
            membership_id=str(uuid.uuid4())[:8].upper()
        )

        # Redirect to edit profile immediately
        messages.info(request, "Welcome! Please complete your profile information to activate your membership.")
        return redirect('members:edit_profile')

    # Check if profile is incomplete
    profile_incomplete = False

    # Check required fields
    if not member.phone_number or member.phone_number.strip() == '':
        profile_incomplete = True

    # Check if address is missing or incomplete
    if not member.address or not all([
        member.address.street, 
        member.address.city, 
        member.address.state, 
        member.address.zip_code
    ]):
        profile_incomplete = True

    # Check if user profile is incomplete
    if not all([
        member.user.first_name,
        member.user.last_name,
        member.user.email
    ]):
        profile_incomplete = True

    if profile_incomplete:
        messages.info(request, "Please complete your profile information to ensure you have full access to all member features.")
        return redirect('members:edit_profile')

    return render(request, 'members/profile.html', {'member': member})

@login_required
def edit_profile(request):
    # Always check if we need to create a member profile
    from .models import Member, Address, MembershipType

    # Get member id from URL if present (for admin users only)
    member_id = request.GET.get('member_id')

    # If a specific member_id is provided, ensure the user has proper permissions
    if member_id and (request.user.is_superuser or is_member_manager(request.user)):
        try:
            member = get_object_or_404(Member, id=member_id)
        except:
            messages.error(request, "Member not found.")
            return redirect('members:member_dashboard')
    else:
        # Regular users can only edit their own profile
        try:
            member = request.user.member
        except Member.DoesNotExist:
            # Create a default address
            address = Address.objects.create(
                street='',
                city='',
                state='',
                zip_code='',
                country='USA'
            )

            # Get the default/free membership type
            try:
                membership_type = MembershipType.objects.filter(billing_frequency='free').first()
                if not membership_type:
                    membership_type = MembershipType.objects.first()
            except:
                membership_type = None

            # Create a new member profile
            member = Member.objects.create(
                user=request.user,
                phone_number='',
                address=address,
                status='pending',
                membership_type=membership_type,
                membership_id=str(uuid.uuid4())[:8].upper()
            )
            messages.info(request, "Welcome! Please complete your profile information to activate your membership.")

    if request.method == 'POST':
        # For admin/managers editing other users' profiles
        if member.user != request.user and not (request.user.is_superuser or is_member_manager(request.user)):
            messages.error(request, "You do not have permission to edit this profile.")
            return redirect('members:member_dashboard')

        profile_form = ProfileForm(request.POST, instance=member.user)
        address_form = AddressForm(request.POST, instance=member.address)
        theme_form = ThemePreferenceForm(request.POST, instance=member)

        if profile_form.is_valid() and address_form.is_valid() and theme_form.is_valid():
            profile_form.save()
            address_form.save()
            theme_form.save()
            member.phone_number = request.POST.get('phone_number')
            member.save()

            messages.success(request, "Profile has been updated successfully.")

            # Redirect based on who made the edit
            if member.user == request.user:
                return redirect('members:member_profile')
            else:
                # Admin/manager edited someone else's profile
                return redirect('members:member_detail', member_id=member.id)
    else:
        profile_form = ProfileForm(instance=member.user)
        address_form = AddressForm(instance=member.address)
        theme_form = ThemePreferenceForm(instance=member)

    return render(request, 'members/edit_profile.html', {
        'profile_form': profile_form,
        'address_form': address_form,
        'theme_form': theme_form,
        'member': member
    })

@login_required
def family_management(request):
    from .models import Member, Address, MembershipType, Child

    try:
        member = request.user.member
    except Member.DoesNotExist:
        # Redirect to member_profile which will handle profile creation
        return redirect('members:member_profile')

    # Check if profile is incomplete
    profile_incomplete = False

    # Check required fields
    if not member.phone_number or member.phone_number.strip() == '':
        profile_incomplete = True

    # Check if address is missing or incomplete
    if not member.address or not all([
        member.address.street, 
        member.address.city, 
        member.address.state, 
        member.address.zip_code
    ]):
        profile_incomplete = True

    # Check if user profile is incomplete
    if not all([
        member.user.first_name,
        member.user.last_name,
        member.user.email
    ]):
        profile_incomplete = True

    if profile_incomplete:
        messages.info(request, "Please complete your profile information to ensure you have full access to all member features.")
        return redirect('members:edit_profile')

    children = Child.objects.filter(parent=member)

    if not member.membership_type.is_family:
        messages.warning(request, "Family management is only available for family membership.")
        return redirect('members:member_dashboard')

    return render(request, 'members/family_management.html', {
        'member': member,
        'children': children
    })

@login_required
def add_child(request):
    try:
        member = request.user.member

        if not member.membership_type.is_family:
            messages.warning(request, "Family management is only available for family membership.")
            return redirect('members:member_dashboard')

        if request.method == 'POST':
            form = ChildForm(request.POST)
            if form.is_valid():
                child = form.save(commit=False)
                child.parent = member
                child.save()
                messages.success(request, "Child added successfully.")
                return redirect('members:family_management')
        else:
            form = ChildForm()

        return render(request, 'members/add_child.html', {
            'form': form,
            'member': member
        })
    except Member.DoesNotExist:
        messages.error(request, "You don't have a member profile. Please contact support.")
        return redirect('members:home')

@login_required
def edit_child(request, child_id):
    try:
        member = request.user.member
        child = get_object_or_404(Child, id=child_id, parent=member)

        if not member.membership_type.is_family:
            messages.warning(request, "Family management is only available for family membership.")
            return redirect('members:member_dashboard')

        if request.method == 'POST':
            form = ChildForm(request.POST, instance=child)
            if form.is_valid():
                form.save()
                messages.success(request, "Child information updated.")
                return redirect('members:family_management')
        else:
            form = ChildForm(instance=child)

        return render(request, 'members/edit_child.html', {
            'form': form,
            'child': child,
            'member': member
        })
    except Member.DoesNotExist:
        messages.error(request, "You don't have a member profile. Please contact support.")
        return redirect('members:home')

@login_required
def delete_child(request, child_id):
    try:
        member = request.user.member
        child = get_object_or_404(Child, id=child_id, parent=member)

        if not member.membership_type.is_family:
            messages.warning(request, "Family management is only available for family membership.")
            return redirect('members:member_dashboard')

        if request.method == 'POST':
            child.delete()
            messages.success(request, "Child removed successfully.")
        else:
            messages.error(request, "Invalid request.")

        return redirect('members:family_management')
    except Member.DoesNotExist:
        messages.error(request, "You don't have a member profile. Please contact support.")
        return redirect('members:home')

@login_required
def child_profile(request, child_id):
    """View child profile"""
    try:
        member = request.user.member
        child = get_object_or_404(Child, id=child_id, parent=member)

        if not member.membership_type.is_family:
            messages.warning(request, "Family management is only available for family membership.")
            return redirect('members:member_dashboard')

        # Get child rank history
        from rank.models import ChildRankHistory
        rank_history = ChildRankHistory.objects.filter(child=child).order_by('-effective_date', '-created_at')

        return render(request, 'members/child_profile.html', {
            'child': child,
            'member': member,
            'rank_history': rank_history
        })
    except Member.DoesNotExist:
        messages.error(request, "You don't have a member profile. Please contact support.")
        return redirect('members:home')

@login_required
def edit_child_profile(request, child_id):
    """Edit child profile"""
    try:
        member = request.user.member
        child = get_object_or_404(Child, id=child_id, parent=member)

        if not member.membership_type.is_family:
            messages.warning(request, "Family management is only available for family membership.")
            return redirect('members:member_dashboard')

        if request.method == 'POST':
            form = ChildForm(request.POST, request.FILES, instance=child)
            if form.is_valid():
                form.save()
                messages.success(request, "Child profile updated successfully.")
                return redirect('members:child_profile', child_id=child.id)
        else:
            form = ChildForm(instance=child)

        return render(request, 'members/edit_child_profile.html', {
            'form': form,
            'child': child,
            'member': member
        })
    except Member.DoesNotExist:
        messages.error(request, "You don't have a member profile. Please contact support.")
        return redirect('members:home')

@user_passes_test(is_member_manager)
def child_detail(request, child_id):
    """Manager view for child details"""
    child = get_object_or_404(Child, id=child_id)

    # Get child rank history
    from rank.models import ChildRankHistory
    rank_history = ChildRankHistory.objects.filter(child=child).order_by('-effective_date', '-created_at')

    return render(request, 'members/manager/child_detail.html', {
        'child': child,
        'rank_history': rank_history
    })


@user_passes_test(is_member_manager)
def convert_child_to_member(request, child_id):
    """Convert a child record into a full member profile.
    Creates a new auth.User and Members.Member using provided details.
    Optionally approves immediately and transfers current child rank to member.
    """
    child = get_object_or_404(Child, id=child_id)

    # Prefill form with child's name
    initial = {
        'first_name': child.first_name,
        'last_name': child.last_name,
    }

    if request.method == 'POST':
        form = ConvertChildToMemberForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data.get('phone_number', '')
            membership_type = form.cleaned_data['membership_type']
            approve_now = form.cleaned_data.get('approve_now', False)

            # Create User with unusable password; admin can send password reset
            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user.set_unusable_password()
            user.save()

            # Create a blank address (consistent with other creation flows)
            address = Address.objects.create(
                street='', city='', state='', zip_code='', country='USA'
            )

            # Create Member
            member = Member.objects.create(
                user=user,
                membership_type=membership_type,
                phone_number=phone_number or '',
                address=address,
                status='pending',
                membership_id=str(uuid.uuid4())[:8].upper()
            )

            # If approve now, run approve method to set expiration and default rank
            if approve_now:
                member.approve(request.user)

            # If child currently has a rank and member has no explicit rank, transfer it
            try:
                from rank.models import MemberRank
                if hasattr(child, 'child_rank_association') and child.child_rank_association:
                    # Only create a MemberRank if member has none
                    try:
                        member.rank_association
                        has_rank = True
                    except Exception:
                        has_rank = False
                    if not has_rank:
                        cr = child.child_rank_association
                        MemberRank.objects.create(
                            member=member,
                            rank=cr.rank,
                            preferred_theme=cr.preferred_theme,
                            effective_date=cr.effective_date,
                            notes=f"Transferred from child record {child.child_id}",
                            assigned_by=request.user
                        )
            except Exception:
                # Fail silently on rank transfer to keep conversion robust
                pass

            # Deactivate the child record but keep for history
            child.status = 'inactive'
            child.save(update_fields=['status'])

            messages.success(request, f"Child '{child.get_full_name()}' has been converted to member '{member.get_full_name()}'.")
            return redirect('members:member_detail', member_id=member.id)
    else:
        form = ConvertChildToMemberForm(initial=initial)

    return render(request, 'members/manager/convert_child_to_member.html', {
        'child': child,
        'form': form,
    })

@login_required
def payment_history(request):
    # Redirect to member_profile which will handle profile creation
    try:
        member = request.user.member
    except Member.DoesNotExist:
        return redirect('members:member_profile')

    # Check if profile is incomplete and redirect to edit profile
    profile_incomplete = not member.phone_number or not member.address or not all([
        member.address.street, member.address.city, member.address.state, member.address.zip_code
    ]) or not all([member.user.first_name, member.user.last_name, member.user.email])

    if profile_incomplete:
        messages.info(request, "Please complete your profile information to ensure you have full access to all member features.")
        return redirect('members:edit_profile')

    from .models import Payment
    payments = Payment.objects.filter(member=member).order_by('-payment_date')

    return render(request, 'members/payment_history.html', {
        'member': member,
        'payments': payments
    })

@login_required
def subscription_management(request):
    # Redirect to member_profile which will handle profile creation
    try:
        member = request.user.member
    except Member.DoesNotExist:
        return redirect('members:member_profile')

    # Check if profile is incomplete and redirect to edit profile
    profile_incomplete = not member.phone_number or not member.address or not all([
        member.address.street, member.address.city, member.address.state, member.address.zip_code
    ]) or not all([member.user.first_name, member.user.last_name, member.user.email])

    if profile_incomplete:
        messages.info(request, "Please complete your profile information to ensure you have full access to all member features.")
        return redirect('members:edit_profile')

    from .models import MembershipType
    membership_types = MembershipType.objects.all()

    return render(request, 'members/subscription_management.html', {
        'member': member,
        'membership_types': membership_types
    })

# Member Manager views
@user_passes_test(is_member_manager)
def manager_dashboard(request):
    pending_count = Member.objects.filter(status='pending').count()
    active_count = Member.objects.filter(status='active').count()
    expired_count = Member.objects.filter(status='expired').count()
    recent_members = Member.objects.order_by('-member_since')[:5]

    return render(request, 'members/manager/dashboard.html', {
        'pending_count': pending_count,
        'active_count': active_count,
        'expired_count': expired_count,
        'recent_members': recent_members
    })

@user_passes_test(is_member_manager)
def pending_approvals(request):
    pending_members = Member.objects.filter(status='pending').order_by('member_since')

    return render(request, 'members/manager/pending_approvals.html', {
        'pending_members': pending_members
    })

@user_passes_test(is_member_manager)
def approve_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)

    if request.method == 'POST':
        member.approve(request.user)
        messages.success(request, f"Member {member} has been approved.")
        return redirect('members:pending_approvals')

    return render(request, 'members/manager/approve_member.html', {
        'member': member
    })

@user_passes_test(is_member_manager)
def reject_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)

    if request.method == 'POST':
        member.reject()
        messages.success(request, f"Member {member} has been rejected.")
        return redirect('members:pending_approvals')

    return render(request, 'members/manager/reject_member.html', {
        'member': member
    })


# FAQ Management Views
@login_required
def faq_management(request):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    categories = FAQCategory.objects.prefetch_related('faqs').all()
    return render(request, 'members/manager/faq_management.html', {
        'categories': categories
    })


@login_required
def faq_management(request):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    categories = FAQCategory.objects.prefetch_related('faqs').all()

    return render(request, 'members/manager/faq_management.html', {
        'categories': categories
    })

@login_required
def add_faq_category(request):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    if request.method == 'POST':
        form = FAQCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "FAQ Category added successfully.")
            return redirect('members:faq_management')
    else:
        form = FAQCategoryForm()

    return render(request, 'members/manager/faq_category_form.html', {
        'form': form,
        'title': 'Add FAQ Category'
    })

@login_required
def edit_faq_category(request, category_id):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    category = get_object_or_404(FAQCategory, id=category_id)

    if request.method == 'POST':
        form = FAQCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "FAQ Category updated successfully.")
            return redirect('members:faq_management')
    else:
        form = FAQCategoryForm(instance=category)

    return render(request, 'members/manager/faq_category_form.html', {
        'form': form,
        'title': 'Edit FAQ Category'
    })

@login_required
def delete_faq_category(request, category_id):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    category = get_object_or_404(FAQCategory, id=category_id)
    faq_count = category.faqs.count()

    if request.method == 'POST':
        # Get the name before deletion for the success message
        category_name = category.name

        # This will automatically delete all associated FAQs due to the CASCADE
        category.delete()

        if faq_count > 0:
            messages.success(request, f"FAQ Category '{category_name}' and its {faq_count} associated FAQ{'s' if faq_count != 1 else ''} have been deleted.")
        else:
            messages.success(request, f"FAQ Category '{category_name}' has been deleted.")

        return redirect('members:faq_management')

    return render(request, 'members/manager/delete_confirmation.html', {
        'object': category,
        'object_type': 'FAQ Category',
        'has_related_items': faq_count > 0,
        'related_count': faq_count,
        'related_type': 'FAQ'
    })

@login_required
def add_faq(request):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            faq = form.save(commit=False)
            faq.created_by = request.user
            faq.updated_by = request.user
            faq.save()
            messages.success(request, "FAQ added successfully.")
            return redirect('members:faq_management')
    else:
        form = FAQForm()
        # Pre-select category if provided in query params
        category_id = request.GET.get('category')
        if category_id:
            try:
                form.fields['category'].initial = int(category_id)
            except (ValueError, TypeError):
                pass

    return render(request, 'members/manager/faq_form.html', {
        'form': form,
        'title': 'Add FAQ'
    })

@login_required
def edit_faq(request, faq_id):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    faq = get_object_or_404(FAQ, id=faq_id)

    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            updated_faq = form.save(commit=False)
            updated_faq.updated_by = request.user
            updated_faq.save()
            messages.success(request, "FAQ updated successfully.")
            return redirect('members:faq_management')
    else:
        form = FAQForm(instance=faq)

    return render(request, 'members/manager/faq_form.html', {
        'form': form,
        'title': 'Edit FAQ'
    })

@login_required
def delete_faq(request, faq_id):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    faq = get_object_or_404(FAQ, id=faq_id)

    if request.method == 'POST':
        faq.delete()
        messages.success(request, "FAQ has been deleted.")
        return redirect('members:faq_management')

    return render(request, 'members/manager/delete_confirmation.html', {
        'object': faq,
        'object_type': 'FAQ'
    })


@login_required
def edit_faq_category(request, category_id):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    category = get_object_or_404(FAQCategory, id=category_id)

    if request.method == 'POST':
        form = FAQCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "FAQ Category updated successfully.")
            return redirect('members:faq_management')
    else:
        form = FAQCategoryForm(instance=category)

    return render(request, 'members/manager/faq_category_form.html', {
        'form': form,
        'title': 'Edit FAQ Category',
        'category': category
    })


@login_required
def delete_faq_category(request, category_id):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    category = get_object_or_404(FAQCategory, id=category_id)

    if request.method == 'POST':
        category.delete()
        messages.success(request, "FAQ Category deleted successfully.")
        return redirect('members:faq_management')

    return render(request, 'members/manager/confirm_delete.html', {
        'object': category,
        'object_name': f'FAQ Category: {category.name}',
        'cancel_url': 'members:faq_management'
    })


@login_required
def add_faq(request):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            faq = form.save(commit=False)
            faq.created_by = request.user
            faq.updated_by = request.user
            faq.save()
            messages.success(request, "FAQ added successfully.")
            return redirect('members:faq_management')
    else:
        form = FAQForm()

    return render(request, 'members/manager/faq_form.html', {
        'form': form,
        'title': 'Add FAQ'
    })


@login_required
def edit_faq(request, faq_id):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    faq = get_object_or_404(FAQ, id=faq_id)

    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            updated_faq = form.save(commit=False)
            updated_faq.updated_by = request.user
            updated_faq.save()
            messages.success(request, "FAQ updated successfully.")
            return redirect('members:faq_management')
    else:
        form = FAQForm(instance=faq)

    return render(request, 'members/manager/faq_form.html', {
        'form': form,
        'title': 'Edit FAQ',
        'faq': faq
    })


@login_required
def delete_faq(request, faq_id):
    if not is_member_manager(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('members:home')

    faq = get_object_or_404(FAQ, id=faq_id)

    if request.method == 'POST':
        faq.delete()
        messages.success(request, "FAQ deleted successfully.")
        return redirect('members:faq_management')

    return render(request, 'members/manager/confirm_delete.html', {
        'object': faq,
        'object_name': f'FAQ: {faq.question}',
        'cancel_url': 'members:faq_management'
    })

from django.core.paginator import Paginator

@login_required
def public_member_list(request):
    """Authenticated member directory with sorting/filtering.
    Shows: name, rank, units, member since, email.
    """
    from units.models import Unit
    from .models import Address
    q = request.GET.get('q', '').strip()
    state = request.GET.get('state', '').strip()
    unit_id = request.GET.get('unit', '').strip()

    members_qs = (
        Member.objects.all()
        .select_related('user', 'address')
        .prefetch_related('unit_memberships__unit', 'rank_association__rank')
    )

    if q:
        members_qs = members_qs.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__email__icontains=q)
        )
    if state:
        members_qs = members_qs.filter(address__state__iexact=state)
    if unit_id:
        try:
            unit_id_int = int(unit_id)
            members_qs = members_qs.filter(unit_memberships__unit_id=unit_id_int, unit_memberships__is_active=True)
        except ValueError:
            pass

    members_qs = members_qs.distinct().order_by('user__last_name', 'user__first_name')

    # Simple pagination (server-side); client-side sorting will re-order current page
    paginator = Paginator(members_qs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filters data
    states = (
        Address.objects.exclude(state='')
        .values_list('state', flat=True)
        .distinct()
        .order_by('state')
    )
    units = Unit.objects.all().order_by('name')

    return render(request, 'members/public_member_list.html', {
        'title': 'Member Directory',
        'page_obj': page_obj,
        'query': q,
        'state_filter': state,
        'unit_filter': unit_id,
        'states': states,
        'units': units,
    })


@login_required
def member_settings(request):
    """
    User-specific settings page:
    - Site theme preference (light/dark)
    - Preferred rank theme limited to themes available for the member's current rank
    Only the current authenticated user can update their own settings.
    """
    # Ensure the user has a Member profile
    member = get_object_or_404(Member.objects.select_related('user'), user=request.user)

    # Prepare preferred theme choices limited to the user's current rank
    # If the user has no rank yet, allow no choices (empty) but keep the field optional
    preferred_theme_field = None
    current_rank = None
    available_themes_qs = None

    try:
        # Current rank association if exists
        mr = member.rank_association  # OneToOne, raises if not present
        current_rank = mr.rank
        # Import Theme and RankImage lazily to avoid circulars
        from rank.models import Theme, RankImage
        available_themes_qs = Theme.objects.filter(rank_images__rank=current_rank, is_active=True).distinct().order_by('name')
    except Exception:
        mr = None

    from django import forms as _forms
    class MemberSettingsForm(_forms.Form):
        SITE_THEME_CHOICES = (
            ('light', 'Light mode'),
            ('dark', 'Dark mode'),
        )
        site_theme = _forms.ChoiceField(choices=SITE_THEME_CHOICES, required=True, label='Site Theme', widget=_forms.Select(attrs={'class': 'form-select'}))
        # preferred_theme defined dynamically below depending on availability

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Dynamically add preferred_theme only if there are themes to choose from
            if available_themes_qs is not None:
                self.fields['preferred_theme'] = _forms.ModelChoiceField(
                    queryset=available_themes_qs,
                    required=False,
                    label='Preferred Rank Theme',
                    widget=_forms.Select(attrs={'class': 'form-select'}),
                    help_text='Select a theme for displaying your rank insignia. Only themes compatible with your current rank are shown.'
                )

    # Initial values
    initial = {
        'site_theme': getattr(member, 'theme_preference', 'dark') or 'dark'
    }
    if 'mr' in locals() and mr is not None:
        initial['preferred_theme'] = mr.preferred_theme_id if mr and mr.preferred_theme_id else None

    if request.method == 'POST':
        form = MemberSettingsForm(request.POST, initial=initial)
        if form.is_valid():
            # Update site theme preference on Member
            member.theme_preference = form.cleaned_data['site_theme']
            member.save(update_fields=['theme_preference'])

            # Update preferred rank theme if applicable
            if 'mr' in locals() and mr is not None and 'preferred_theme' in form.fields:
                new_theme = form.cleaned_data.get('preferred_theme')
                # Only save if changed
                if (mr.preferred_theme_id or None) != (new_theme.id if new_theme else None):
                    mr.preferred_theme = new_theme
                    # Record who assigned the change
                    mr.assigned_by = request.user
                    mr.save()

            messages.success(request, 'Your settings have been updated.')
            return redirect('members:member_settings')
    else:
        form = MemberSettingsForm(initial=initial)

    # Gather context for template display
    rank_info = None
    if 'mr' in locals() and mr is not None:
        rank_info = {
            'paygrade': mr.rank.paygrade,
            'short_name': mr.rank.short_name,
            'long_name': mr.rank.long_name,
        }

    return render(request, 'members/member_settings.html', {
        'title': 'My Settings',
        'form': form,
        'rank_info': rank_info,
        'has_rank': ('mr' in locals() and mr is not None),
    })


def public_member_detail(request, member_id):
    """Public, read-only member profile page.
    Shows basic info and active units with links to unit public profiles.
    """
    member = get_object_or_404(
        Member.objects.select_related('user', 'rank_association__rank')
        .prefetch_related('unit_memberships__unit'),
        id=member_id
    )
    active_memberships = [um for um in member.unit_memberships.all() if um.is_active]
    return render(request, 'members/public_member_detail.html', {
        'member': member,
        'active_memberships': active_memberships,
        'title': f"{member.user.get_full_name() or member.user.username} – Profile",
    })

@user_passes_test(is_member_manager)
def member_list(request):
    status_filter = request.GET.get('status', '')
    query = request.GET.get('q', '')

    members = Member.objects.all().select_related('user')

    if status_filter:
        members = members.filter(status=status_filter)

    if query:
        members = members.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) | 
            Q(user__email__icontains=query) | 
            Q(phone_number__icontains=query) |
            Q(membership_id__icontains=query)
        )

    # Add pagination
    paginator = Paginator(members, 20)  # Show 20 members per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'members/manager/member_list.html', {
        'members': members,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'query': query,
        'title': 'Member List'
    })

@user_passes_test(is_member_manager)
def member_detail(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    children = Child.objects.filter(parent=member)
    payments = Payment.objects.filter(member=member).order_by('-payment_date')

    # Get rank history from the rank app
    from rank.models import MemberRankHistory
    rank_history = MemberRankHistory.objects.filter(member=member).order_by('-effective_date', '-created_at')

    # Check if the user is a manager
    is_manager = member.user.groups.filter(name='Member Manager').exists()

    # Create an edit profile URL with the member_id parameter
    edit_profile_url = f"{reverse('members:edit_profile')}?member_id={member.id}"

    return render(request, 'members/manager/member_detail.html', {
        'member': member,
        'children': children,
        'payments': payments,
        'rank_history': rank_history,
        'is_manager': is_manager,
        'edit_profile_url': edit_profile_url
    })

@user_passes_test(lambda u: u.is_superuser)
def update_user_roles(request, member_id):
    """Update user roles for a member"""
    member = get_object_or_404(Member, id=member_id)
    user = member.user

    if request.method == 'POST':
        # Update superuser status
        is_superuser = 'is_superuser' in request.POST
        user.is_superuser = is_superuser

        # Update staff status
        is_staff = 'is_staff' in request.POST
        user.is_staff = is_staff

        # Update manager status
        is_manager = 'is_manager' in request.POST
        manager_group, created = Group.objects.get_or_create(name='manager')

        if is_manager:
            user.groups.add(manager_group)
        else:
            user.groups.remove(manager_group)

        # Update member manager status
        is_member_manager = 'is_member_manager' in request.POST
        member_manager_group, created = Group.objects.get_or_create(name='member_manager')

        if is_member_manager:
            user.groups.add(member_manager_group)
        else:
            user.groups.remove(member_manager_group)

        # Update rank manager status
        is_rank_manager = 'is_rank_manager' in request.POST
        rank_manager_group, created = Group.objects.get_or_create(name='rank_manager')

        if is_rank_manager:
            user.groups.add(rank_manager_group)
        else:
            user.groups.remove(rank_manager_group)

        # Save the user object
        user.save()

        messages.success(request, f"User roles for {user.first_name} {user.last_name} have been updated.")
    else:
        messages.error(request, "Only POST requests are allowed for this action.")

    return redirect('members:member_detail', member_id=member_id)

# Payment processing views
@login_required
def process_payment(request):
    if request.method == 'POST':
        member = request.user.member
        membership_type_id = request.POST.get('membership_type')
        membership_type = get_object_or_404(MembershipType, id=membership_type_id)

        # In a real implementation, this would integrate with a payment gateway
        # For now, we'll simulate a successful payment

        payment = Payment.objects.create(
            member=member,
            amount=membership_type.price,
            status='completed',
            payment_method='Credit Card',
            transaction_id=str(uuid.uuid4())[:12].upper()
        )

        # Update member's subscription
        member.membership_type = membership_type
        member.set_expiration_date()
        member.status = 'active'
        member.save()

        messages.success(request, "Payment processed successfully. Your membership has been updated.")
        return redirect('members:payment_complete')

    return redirect('members:subscription_management')

@login_required
def payment_complete(request):
    return render(request, 'members/payment_complete.html')

@login_required
def payment_failed(request):
    return render(request, 'members/payment_failed.html')
