from django.urls import path
from . import views

urlpatterns = [
    path('', views.worklog_list, name='worklog_list'),
    path('create/', views.worklog_create, name='worklog_create'),
    path('<int:pk>/edit/', views.worklog_update, name='worklog_update'),
    path('<int:pk>/delete/', views.worklog_delete, name='worklog_delete'),
    
    # カテゴリ管理
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # 案件管理
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('summary/', views.monthly_summary, name='monthly_summary'),
    path('import/', views.import_csv, name='import_csv'),
    path('setting/', views.admin_dashboard, name='admin_dashboard'),
]
