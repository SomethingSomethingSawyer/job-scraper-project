from django.core.management.base import BaseCommand
from scraper.scraper_engine import UniversalJobScraper


class Command(BaseCommand):
    help = 'Scrape job listings from configured sites'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--urls',
            nargs='+',
            type=str,
            help='URLs to scrape (space-separated)'
        )
    
    def handle(self, *args, **options):
        urls = options.get('urls') or [
            "https://www.usajobs.gov/Search/Results?k=internship",
            "https://careers.stanford.edu/",
        ]
        
        self.stdout.write(f"Starting scrape of {len(urls)} sites...")
        
        scraper = UniversalJobScraper()
        stats = scraper.scrape_multiple_sites(urls)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nScraping complete!\n"
                f"Found: {stats['found']}\n"
                f"Created: {stats['created']}\n"
                f"Updated: {stats['updated']}"
            )
        )