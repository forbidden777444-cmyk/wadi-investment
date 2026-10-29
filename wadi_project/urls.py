from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("register/", views.register_agent, name="register"),
    path("login/", views.agent_login, name="login"),
    path("logout/", views.agent_logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("customers/", views.customer_list, name="customers"),
    path("customers/new/", views.customer_create, name="customer_create"),
    path("loans/", views.loan_list, name="loans"),
    path("loans/new/", views.loan_create, name="loan_create"),
    path("loans/<int:loan_id>/payments/new/", views.payment_create, name="payment_create"),
]