from django.contrib import admin
from .models import AgentProfile

@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ("agent_code", "user", "phone", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("agent_code", "user__username", "user__first_name", "user__last_name", "phone")
    list_editable = ("status",)
    readonly_fields = ("created_at",)
    actions = ["approve_agents", "reject_agents"]

    @admin.action(description="Approve selected agents")
    def approve_agents(self, request, queryset):
        queryset.update(status=AgentProfile.ApprovalStatus.APPROVED)

    @admin.action(description="Reject selected agents")
    def reject_agents(self, request, queryset):
        queryset.update(status=AgentProfile.ApprovalStatus.REJECTED)
