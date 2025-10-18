from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'rank'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.rank_dashboard, name='dashboard'),

    # Rank management
    path('ranks/', views.rank_list, name='rank_list'),
    path('ranks/create/', views.rank_create, name='rank_create'),
    path('ranks/<int:pk>/edit/', views.rank_edit, name='rank_edit'),
    path('ranks/<int:pk>/delete/', views.rank_delete, name='rank_delete'),

    # Theme management
    path('themes/', views.theme_list, name='theme_list'),
    path('themes/create/', views.theme_create, name='theme_create'),
    path('themes/<int:pk>/edit/', views.theme_edit, name='theme_edit'),
    path('themes/<int:pk>/delete/', views.theme_delete, name='theme_delete'),
    path('themes/<int:pk>/', views.theme_detail, name='theme_detail'),

    # Rank image management
    path('themes/<int:theme_id>/add-rank-image/', views.rank_image_create, name='rank_image_create'),
    path('rank-images/<int:pk>/edit/', views.rank_image_edit, name='rank_image_edit'),
    path('rank-images/<int:pk>/delete/', views.rank_image_delete, name='rank_image_delete'),

    # Genre management
    path('genres/', views.genre_list, name='genre_list'),
    path('genres/create/', views.genre_create, name='genre_create'),
    path('genres/<int:pk>/edit/', views.genre_edit, name='genre_edit'),
    path('genres/<int:pk>/delete/', views.genre_delete, name='genre_delete'),

    # Branch management
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/create/', views.branch_create, name='branch_create'),
    path('branches/<int:pk>/edit/', views.branch_edit, name='branch_edit'),
    path('branches/<int:pk>/delete/', views.branch_delete, name='branch_delete'),

    # Settings management
    path('settings/', views.settings_edit, name='settings_edit'),

    # People Rank Management (unified members and children)
    path('people/', views.people_list, name='people_list'),
    path('people/<str:person_type>/<int:person_id>/assign/', views.person_rank_assign, name='person_rank_assign'),
    path('people/<str:person_type>/<int:person_id>/history/', views.person_rank_history, name='person_rank_history'),

    # Legacy redirects for backward compatibility
    path('members/', views.people_list, name='member_list'),
    path('children/', views.people_list, name='child_list'),
    path('members/<int:member_id>/assign-rank/', lambda request, member_id: redirect('rank:person_rank_assign', 'member', member_id), name='member_rank_assign'),
    path('members/<int:member_id>/rank-history/', lambda request, member_id: redirect('rank:person_rank_history', 'member', member_id), name='member_rank_history'),
    path('children/<int:child_id>/assign/', lambda request, child_id: redirect('rank:person_rank_assign', 'child', child_id), name='child_rank_assign'),
    path('children/<int:child_id>/history/', lambda request, child_id: redirect('rank:person_rank_history', 'child', child_id), name='child_rank_history'),

    path('api/get-themes/', views.get_themes_for_selection, name='get_themes_ajax'),
    path('ranks/update-order/', views.update_rank_order, name='update_rank_order'),
]
