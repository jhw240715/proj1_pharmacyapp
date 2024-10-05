from django.urls import path
from . import views
from .views import CustomLoginView, BoardUpdateView


urlpatterns = [
    path('', views.home, name='home'),


    # 유저
    path('signup/', views.signup_view, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # 약국
    path('pharmacy-list/', views.pharmacy_list, name='pharmacy_list'),
    path('pharmacy/<int:p_id>/', views.pharmacy_detail, name='pharmacy_detail'),
    path('nearby/', views.nearby_pharmacies, name='nearby_pharmacies'),

    # 약국 보드(리뷰) & 스코어
    path('board-list/', views.board_list_view, name='board_list'),
    path('board/<int:pk>/', views.board_detail_view, name='board_detail'),
    path('board/<int:pk>/update/', BoardUpdateView.as_view(), name='board_update'),
    path('create/<int:pharmacy_id>/', views.create_board_and_score, name='create_board_and_score'),
    path('board/<int:board_id>/delete/', views.delete_board_and_score, name='delete_board_and_score'),

    path('visualize_scores/', views.visualize_scores, name='visualize_scores'),
    path('visualize_scores_page/', views.visualize_scores_page, name='visualize_scores_page'),
    ]


