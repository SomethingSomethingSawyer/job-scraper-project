"""
Celery configuration for job_scraper project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_scraper.settings')

app = Celery('job_scraper')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Periodic task schedule
app.conf.beat_schedule = {
    'scrape-jobs-daily': {
        'task': 'scraper.tasks.scrape_all_sites',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
    },
    'cleanup-old-jobs-weekly': {
        'task': 'scraper.tasks.cleanup_old_jobs',
        'schedule': crontab(day_of_week=0, hour=1, minute=0),  # Sunday at 1 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')