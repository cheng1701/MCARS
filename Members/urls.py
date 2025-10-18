from django.urls import path
from . import views
from . import profile_views

app_name = 'members'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('ift-mcars/', views.membership_plans, name='membership_plans'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),

    # Public member profile
    path('public/<int:member_id>/', views.public_member_detail, name='public_member_detail'),

    # Authenticated public directory
    path('directory/', views.public_member_list, name='public_member_list'),

    # Authentication
    path('register/', views.register, name='register'),
    path('register/success/', views.registration_success, name='registration_success'),
    path('logout/', views.logout_user, name='logout'),

    # Member portal
    path('member/dashboard/', views.member_dashboard, name='member_dashboard'),
    path('member/profile/', views.member_profile, name='member_profile'),
    path('member/profile/edit/', views.edit_profile, name='edit_profile'),
    path('member/profile/update-image/', profile_views.update_profile_image, name='update_profile_image'),
    path('member/profile/remove-image/', profile_views.remove_profile_image, name='remove_profile_image'),
    path('member/settings/', views.member_settings, name='member_settings'),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    path('member/family/', views.family_management, name='family_management'),
    path('member/family/add_child/', views.add_child, name='add_child'),
    path('member/family/edit_child/<int:child_id>/', views.edit_child, name='edit_child'),
    path('member/family/delete_child/<int:child_id>/', views.delete_child, name='delete_child'),
    path('member/family/child_profile/<int:child_id>/', views.child_profile, name='child_profile'),
    path('member/family/edit_child_profile/<int:child_id>/', views.edit_child_profile, name='edit_child_profile'),
    path('manager/child_detail/<int:child_id>/', views.child_detail, name='child_detail'),
    path('manager/child/<int:child_id>/convert/', views.convert_child_to_member, name='convert_child_to_member'),
    path('member/payments/', views.payment_history, name='payment_history'),
    path('member/subscription/', views.subscription_management, name='subscription_management'),

    # Member Manager portal
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('manager/approve/<int:member_id>/', views.approve_member, name='approve_member'),
    path('manager/reject/<int:member_id>/', views.reject_member, name='reject_member'),
    path('manager/members/', views.member_list, name='member_list'),
    path('manager/member/<int:member_id>/', views.member_detail, name='member_detail'),
    path('manager/member/<int:member_id>/update-roles/', views.update_user_roles, name='update_user_roles'),

    # FAQ Management
    path('manager/faqs/', views.faq_management, name='faq_management'),
    path('manager/faqs/category/add/', views.add_faq_category, name='add_faq_category'),
    path('manager/faqs/category/edit/<int:category_id>/', views.edit_faq_category, name='edit_faq_category'),
    path('manager/faqs/category/delete/<int:category_id>/', views.delete_faq_category, name='delete_faq_category'),
    path('manager/faqs/add/', views.add_faq, name='add_faq'),
    path('manager/faqs/edit/<int:faq_id>/', views.edit_faq, name='edit_faq'),
    path('manager/faqs/delete/<int:faq_id>/', views.delete_faq, name='delete_faq'),

    # Payment processing
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/complete/', views.payment_complete, name='payment_complete'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
]
