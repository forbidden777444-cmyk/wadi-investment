from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from .forms import AgentRegistrationForm, CustomerForm, LoanForm, PaymentForm
from .models import AgentProfile, Customer, Loan, Payment


def home(request):
    return redirect("dashboard" if request.user.is_authenticated else "login")


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
        user = authenticate(request, username=request.POST.get("username", "").strip(), password=request.POST.get("password", ""))
        if user is not None:
            try:
                profile = user.agentprofile
            except AgentProfile.DoesNotExist:
                profile = None
            if user.is_superuser or (profile and profile.status == AgentProfile.ApprovalStatus.APPROVED):
                login(request, user)
                return redirect("dashboard")
            error = ("This agent registration was not approved. Please contact the administrator." if profile and profile.status == AgentProfile.ApprovalStatus.REJECTED else "Your account is awaiting administrator approval.")
        else:
            error = "Incorrect username or password."
    return render(request, "core/login.html", {"error": error})


def agent_logout(request):
    logout(request)
    return redirect("login")


def approved_user(view_func):
    """Require a signed-in superuser or an administrator-approved agent."""
    from functools import wraps
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            profile = request.user.agentprofile
        except AgentProfile.DoesNotExist:
            logout(request)
            return redirect("login")
        if profile.status != AgentProfile.ApprovalStatus.APPROVED:
            logout(request)
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapped


@approved_user
def dashboard(request):
    today = timezone.localdate()
    loans = Loan.objects.all()
    total_lent = sum((loan.principal for loan in loans), Decimal("0.00"))
    total_outstanding = sum((loan.balance for loan in loans), Decimal("0.00"))
    active_loans = [loan for loan in loans if loan.balance > 0]
    overdue_loans = [loan for loan in active_loans if loan.is_overdue]
    collected_today = Payment.objects.filter(paid_on=today).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    context = {"customer_count": Customer.objects.count(), "active_loan_count": len(active_loans),
        "overdue_count": len(overdue_loans), "total_lent": total_lent, "total_outstanding": total_outstanding,
        "collected_today": collected_today, "recent_loans": loans.select_related("customer", "issued_by")[:6]}
    return render(request, "core/dashboard.html", context)


@approved_user
def customer_list(request):
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.all()
    if query:
        customers = customers.filter(first_name__icontains=query) | customers.filter(last_name__icontains=query) | customers.filter(phone__icontains=query) | customers.filter(national_id__icontains=query)
    return render(request, "core/customers.html", {"customers": customers.distinct(), "query": query})


@approved_user
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        customer = form.save(commit=False)
        customer.created_by = request.user
        customer.save()
        messages.success(request, f"Customer {customer.first_name} {customer.last_name} was added.")
        return redirect("customers")
    return render(request, "core/form_page.html", {"form": form, "title": "Register customer", "intro": "Add the customer's contact and identification details.", "button_text": "Save customer"})


@approved_user
def loan_list(request):
    loans = Loan.objects.select_related("customer", "issued_by").prefetch_related("payments")
    status = request.GET.get("status", "")
    if status == "active":
        loans = [loan for loan in loans if loan.balance > 0]
    elif status == "paid":
        loans = [loan for loan in loans if loan.balance <= 0]
    elif status == "overdue":
        loans = [loan for loan in loans if loan.is_overdue]
    return render(request, "core/loans.html", {"loans": loans, "status_filter": status})


@approved_user
def loan_create(request):
    form = LoanForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        loan = form.save(commit=False)
        loan.issued_by = request.user
        loan.interest_rate = Decimal("25.00")
        loan.term_days = 30
        loan.save()
        messages.success(request, f"Loan created. Total repayment is KSh {loan.total_due:,.2f}; expected daily payment is KSh {loan.daily_installment:,.2f} for 30 days.")
        return redirect("loans")
    return render(request, "core/form_page.html", {"form": form, "title": "Issue a loan", "intro": "Interest is fixed at 25% of the original loan. Repayment term is 30 days.", "button_text": "Issue loan"})


@approved_user
def payment_create(request, loan_id):
    loan = get_object_or_404(Loan.objects.select_related("customer").prefetch_related("payments"), pk=loan_id)
    if loan.balance <= 0:
        messages.info(request, "This loan is already fully paid.")
        return redirect("loans")
    form = PaymentForm(request.POST or None, loan=loan)
    if request.method == "POST" and form.is_valid():
        payment = form.save(commit=False)
        payment.loan = loan
        payment.recorded_by = request.user
        payment.save()
        # Re-fetch so the balance includes the newly saved payment, not the earlier prefetched cache.
        updated_loan = Loan.objects.get(pk=loan.pk)
        messages.success(request, f"Payment of KSh {payment.amount:,.2f} recorded. Remaining balance: KSh {updated_loan.balance:,.2f}.")
        return redirect("loans")
    return render(request, "core/form_page.html", {"form": form, "title": "Record daily payment", "intro": f"{loan.customer} · Total due KSh {loan.total_due:,.2f} · Paid KSh {loan.amount_paid:,.2f} · Balance KSh {loan.balance:,.2f} · Due today including arrears KSh {loan.next_payment_due:,.2f}", "button_text": "Record payment", "loan": loan})
