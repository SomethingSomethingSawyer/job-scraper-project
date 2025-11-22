from celery import shared_task
from .scraper_engine import UniversalJobScraper
from datetime import timedelta
from django.utils import timezone
from .models import JobListing


@shared_task
def scrape_all_sites():
    """Celery task to scrape all configured sites"""
    urls = [
        "https://www.usajobs.gov/Search/Results?k=internship",
        "https://careers.stanford.edu/",
        "https://www.idealist.org/en/careers",
    ]
    
    scraper = UniversalJobScraper()
    stats = scraper.scrape_multiple_sites(urls)
    
    return {
        'status': 'completed',
        'found': stats['found'],
        'created': stats['created'],
        'updated': stats['updated']
    }


@shared_task
def cleanup_old_jobs():
    """Remove closed jobs older than 90 days"""
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count = JobListing.objects.filter(
        closed=True,
        date_updated__lt=cutoff_date
    ).delete()[0]
    
    return f"Deleted {deleted_count} old jobs"