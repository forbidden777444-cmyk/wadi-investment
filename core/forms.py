from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import (
    AgentProfile,
    Customer,
    Loan,
    Payment,
)


class AgentRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name")
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=30)
    agent_code = forms.CharField(max_length=30, label="Agent ID")
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm password"
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already in use.")
        return username

    def clean_agent_code(self):
        code = self.cleaned_data["agent_code"].strip().upper()
        if AgentProfile.objects.filter(agent_code__iexact=code).exists():
            raise forms.ValidationError(
                "That Agent ID is already registered."
            )
        return code

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The passwords do not match.")

        if password1:
            validate_password(password1)

        return cleaned

    def save(self):
        data = self.cleaned_data

        user = User.objects.create_user(
            username=data["username"],
            email=data.get("email", ""),
            password=data["password1"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )

        AgentProfile.objects.create(
            user=user,
            phone=data["phone"],
            agent_code=data["agent_code"],
            status=AgentProfile.ApprovalStatus.PENDING,
        )

        return user


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "first_name",
            "last_name",
            "phone",
            "national_id",
            "address",
        ]


class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ["customer", "principal"]

    def clean_principal(self):
        principal = self.cleaned_data["principal"]

        if principal <= 0:
            raise forms.ValidationError(
                "The loan amount must be greater than zero."
            )

        return principal


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "paid_on", "notes"]
        widgets = {
            "paid_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, loan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.loan = loan

    def clean_amount(self):
        amount = self.cleaned_data["amount"]

        if amount <= 0:
            raise forms.ValidationError(
                "The payment must be greater than zero."
            )

        if self.loan is not None and amount > self.loan.balance:
            raise forms.ValidationError(
                "The payment cannot exceed the outstanding balance."
            )

        return amount