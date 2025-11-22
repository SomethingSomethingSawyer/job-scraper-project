from django.contrib import admin
from django.utils.html import format_html
from .models import JobListing, EmailSubscriber, ScrapingLog

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'job_type', 'date_scraped', 'closed', 'source_domain']
    list_filter = ['job_type', 'closed', 'sectors', 'work_format', 'date_scraped']
    search_fields = ['title', 'organization', 'locations']
    actions = ['mark_as_closed', 'mark_as_open', 'delete_old_jobs']
    date_hierarchy = 'date_scraped'
    
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(closed=True)
        self.message_user(request, f'{updated} jobs marked as closed')
    mark_as_closed.short_description = "Mark selected jobs as closed"
    
    def mark_as_open(self, request, queryset):
        updated = queryset.update(closed=False)
        self.message_user(request, f'{updated} jobs marked as open')
    mark_as_open.short_description = "Mark selected jobs as open"
    
    def delete_old_jobs(self, request, queryset):
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=90)
        old = queryset.filter(date_scraped__lt=cutoff)
        count = old.count()
        old.delete()
        self.message_user(request, f'Deleted {count} jobs older than 90 days')
    delete_old_jobs.short_description = "Delete jobs older than 90 days"

@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    list_display = ['started_at', 'status', 'jobs_found', 'jobs_added', 'jobs_updated', 'completed_at']
    list_filter = ['status', 'started_at']
    readonly_fields = ['started_at', 'completed_at', 'status', 'jobs_found', 'jobs_added', 'jobs_updated']
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation

@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active']
    list_filter = ['is_active', 'job_types', 'sectors']
    search_fields = ['email']