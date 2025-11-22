from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings


class JobListing(models.Model):
    """Main job listing model with comprehensive fields"""
    
    JOB_TYPE_CHOICES = [
        ('internship', 'Internship'),
        ('job', 'Full-Time Job'),
        ('fellowship', 'Fellowship'),
    ]
    
    WORK_FORMAT_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-Site'),
    ]
    
    # Basic Info
    title = models.CharField(max_length=500)
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES, default='job')
    organization = models.CharField(max_length=500)
    
    # Company Details
    company_link = models.URLField(max_length=500, blank=True, null=True)
    company_logo = models.URLField(max_length=500, blank=True, null=True)
    
    # Location & Format
    locations = ArrayField(models.CharField(max_length=200), blank=True, default=list)
    work_format = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list
    )
    
    # Geographic coordinates for distance calculation
    zip_codes = ArrayField(models.CharField(max_length=10), blank=True, default=list)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Skills & Sectors
    technical_skills = models.JSONField(default=dict, blank=True)
    soft_skills = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    sectors = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    
    # Links & Status
    apply_link = models.URLField(max_length=500)
    source_domain = models.CharField(max_length=200, blank=True)
    closed = models.BooleanField(default=False)
    sponsorship_required = models.BooleanField(default=False)
    
    # Dates
    posting_date = models.CharField(max_length=100, blank=True)
    date_scraped = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_scraped']
        indexes = [
            models.Index(fields=['job_type', 'closed']),
            models.Index(fields=['organization']),
            models.Index(fields=['date_scraped']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.organization} - {self.title}"


class EmailSubscriber(models.Model):
    """Email subscribers for job alerts"""
    email = models.EmailField(unique=True)
    subscribed_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Preferences
    job_types = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="Preferred job types (internship, job, fellowship)"
    )
    sectors = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Preferred sectors"
    )
    
    # Location preferences
    zip_code = models.CharField(max_length=10, blank=True)
    max_distance_miles = models.IntegerField(null=True, blank=True, help_text="Maximum distance in miles")
    
    def __str__(self):
        return self.email


class ScrapingLog(models.Model):
    """Track scraping runs and their results"""
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='running')
    sites_scraped = ArrayField(models.CharField(max_length=500), default=list)
    jobs_found = models.IntegerField(default=0)
    jobs_added = models.IntegerField(default=0)
    jobs_updated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Scrape {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.status}"


@receiver(post_save, sender=JobListing)
def send_email_on_new_job(sender, instance, created, **kwargs):
    """Send email notifications when new jobs are posted"""
    if created and not instance.closed:
        from geopy.distance import geodesic
        import pgeocode
        
        subscribers = EmailSubscriber.objects.filter(is_active=True)
        
        for subscriber in subscribers:
            # Check preferences
            if subscriber.job_types and instance.job_type not in subscriber.job_types:
                continue
            if subscriber.sectors and not any(s in instance.sectors for s in subscriber.sectors):
                continue
            
            # Check distance if subscriber has location preferences
            if subscriber.zip_code and subscriber.max_distance_miles and instance.latitude and instance.longitude:
                try:
                    nomi = pgeocode.Nominatim('us')
                    user_location = nomi.query_postal_code(subscriber.zip_code)
                    if user_location is not None:
                        user_coords = (user_location.latitude, user_location.longitude)
                        job_coords = (instance.latitude, instance.longitude)
                        distance = geodesic(user_coords, job_coords).miles
                        
                        if distance > subscriber.max_distance_miles:
                            continue  # Too far away
                except:
                    pass  # If distance calc fails, still send email
            
            # Send email
            subject = f"New {instance.job_type.title()}: {instance.organization} - {instance.title}"
            
            message = f"""
New Job Alert!

Title: {instance.title}
Organization: {instance.organization}
Job Type: {instance.job_type.title()}
Locations: {', '.join(instance.locations)}
Work Format: {', '.join(instance.work_format)}
Sectors: {', '.join(instance.sectors)}

Apply: {instance.apply_link}

---
This is an automated notification from Job Scraper.
            """
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[subscriber.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send email: {e}")