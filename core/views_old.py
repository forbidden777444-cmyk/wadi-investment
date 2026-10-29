from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import AgentRegistrationForm
from .models import AgentProfile

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")

def register_agent(request):
    if request.method == "POST":
        form = AgentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration submitted. An administrator must approve your account before you can log in.")
            return redirect("login")
    else:
        form = AgentRegistrationForm()
    return render(request, "core/register.html", {"form": form})

def agent_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                profile = user.agentprofile
            except AgentProfile.DoesNotExist:
                profile = None
            if user.is_superuser or (profile and profile.status == AgentProfile.ApprovalStatus.APPROVED):
                login(request, user)
                return redirect("dashboard")
            if profile and profile.status == AgentProfile.ApprovalStatus.REJECTED:
                error = "This agent registration was not approved. Please contact the administrator."
            else:
                error = "Your account is awaiting administrator approval."
        else:
            error = "Incorrect username or password."
    return render(request, "core/login.html", {"error": error})

def agent_logout(request):
    logout(request)
    return redirect("login")

@login_required
def dashboard(request):
    if not request.user.is_superuser:
        try:
            profile = request.user.agentprofile
        except AgentProfile.DoesNotExist:
            logout(request)
            return redirect("login")
        if profile.status != AgentProfile.ApprovalStatus.APPROVED:
            logout(request)
            return redirect("login")
    return render(request, "core/dashboard.html")
