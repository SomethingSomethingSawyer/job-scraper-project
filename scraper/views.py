from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from geopy.distance import geodesic
import pgeocode
from collections import Counter
from .models import JobListing, EmailSubscriber, ScrapingLog
from .serializers import (
    JobListingSerializer, 
    EmailSubscriberSerializer,
    ScrapingLogSerializer
)
from .scraper_engine import UniversalJobScraper


# API ViewSets
class JobListingViewSet(viewsets.ModelViewSet):
    queryset = JobListing.objects.all()
    serializer_class = JobListingSerializer
    
    def get_queryset(self):
        queryset = JobListing.objects.all()
        
        job_type = self.request.query_params.get('job_type', None)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        sector = self.request.query_params.get('sector', None)
        if sector:
            queryset = queryset.filter(sectors__contains=[sector])
        
        work_format = self.request.query_params.get('work_format', None)
        if work_format:
            queryset = queryset.filter(work_format__contains=[work_format])
        
        closed = self.request.query_params.get('closed', None)
        if closed is not None:
            queryset = queryset.filter(closed=closed.lower() == 'true')
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        return queryset.order_by('-date_scraped')
    
    @action(detail=False, methods=['post'])
    def trigger_scrape(self, request):
        urls = request.data.get('urls', [])
        
        if not urls:
            return Response(
                {"error": "No URLs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            scraper = UniversalJobScraper()
            stats = scraper.scrape_multiple_sites(urls)
            
            return Response({
                "message": "Scraping completed successfully",
                "stats": stats
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailSubscriberViewSet(viewsets.ModelViewSet):
    queryset = EmailSubscriber.objects.all()
    serializer_class = EmailSubscriberSerializer
    lookup_field = 'email'


class ScrapingLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ScrapingLog.objects.all()
    serializer_class = ScrapingLogSerializer


# Template Views with Distance Filtering
def calculate_statistics(jobs_queryset):
    """Calculate statistics for a set of jobs"""
    total_jobs = jobs_queryset.count()
    
    if total_jobs == 0:
        return None
    
    # Job type distribution
    job_types = jobs_queryset.values('job_type').annotate(count=Count('id'))
    job_type_stats = {item['job_type']: item['count'] for item in job_types}
    
    # Sector distribution
    all_sectors = []
    for job in jobs_queryset:
        all_sectors.extend(job.sectors)
    sector_counts = Counter(all_sectors)
    top_sectors = sector_counts.most_common(5)
    
    # Skills statistics
    all_technical_skills = []
    all_soft_skills = []
    for job in jobs_queryset:
        if job.technical_skills:
            for category, skills in job.technical_skills.items():
                all_technical_skills.extend(skills)
        all_soft_skills.extend(job.soft_skills)
    
    technical_skill_counts = Counter(all_technical_skills)
    top_technical_skills = technical_skill_counts.most_common(10)
    
    soft_skill_counts = Counter(all_soft_skills)
    top_soft_skills = soft_skill_counts.most_common(10)
    
    # Work format distribution
    all_formats = []
    for job in jobs_queryset:
        all_formats.extend(job.work_format)
    format_counts = Counter(all_formats)
    
    # Average skills per job
    skill_counts = []
    for job in jobs_queryset:
        total_skills = len(all_technical_skills) + len(job.soft_skills)
        skill_counts.append(total_skills)
    avg_skills = sum(skill_counts) / len(skill_counts) if skill_counts else 0
    
    return {
        'total_jobs': total_jobs,
        'job_type_stats': job_type_stats,
        'top_sectors': top_sectors,
        'top_technical_skills': top_technical_skills,
        'top_soft_skills': top_soft_skills,
        'work_format_stats': dict(format_counts),
        'avg_skills_per_job': round(avg_skills, 1),
    }


def home(request):
    """Homepage with dashboard"""
    total_jobs = JobListing.objects.filter(closed=False).count()
    recent_logs = ScrapingLog.objects.all()[:5]
    
    return render(request, 'home.html', {
        'total_jobs': total_jobs,
        'recent_logs': recent_logs,
    })


def job_list(request):
    """Browse all jobs with filters and distance"""
    jobs = JobListing.objects.filter(closed=False)
    
    # Mode selection
    search_mode = request.GET.get('mode', 'nationwide')
    
    # LOCAL MODE: Distance-based filtering
    if search_mode == 'local':
        user_zip = request.GET.get('zip_code', '')
        max_distance = request.GET.get('max_distance', '')
        
        if user_zip and max_distance:
            try:
                nomi = pgeocode.Nominatim('us')
                user_location = nomi.query_postal_code(user_zip)
                
                if user_location is not None and not user_location.isna().all():
                    user_coords = (user_location.latitude, user_location.longitude)
                    max_dist_miles = float(max_distance)
                    
                    # Filter jobs by distance
                    nearby_jobs = []
                    for job in jobs:
                        if job.latitude and job.longitude:
                            job_coords = (job.latitude, job.longitude)
                            distance = geodesic(user_coords, job_coords).miles
                            if distance <= max_dist_miles:
                                job.distance = round(distance, 1)
                                nearby_jobs.append(job)
                    
                    jobs = nearby_jobs
                    jobs.sort(key=lambda x: x.distance)
                else:
                    messages.warning(request, f"Could not find location for zip code: {user_zip}")
            except Exception as e:
                messages.error(request, f"Error calculating distances: {str(e)}")
    
    # NATIONWIDE MODE: Standard filtering
    else:
        search = request.GET.get('search', '')
        if search:
            jobs = jobs.filter(title__icontains=search)
        
        job_type = request.GET.get('job_type', '')
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        
        work_format = request.GET.get('work_format', '')
        if work_format:
            jobs = jobs.filter(work_format__contains=[work_format])
        
        sector = request.GET.get('sector', '')
        if sector:
            jobs = jobs.filter(sectors__contains=[sector])
        
        state = request.GET.get('state', '')
        if state:
            jobs = jobs.filter(locations__icontains=state)
        
        jobs = jobs.order_by('-date_scraped')
    
    # Calculate statistics
    if isinstance(jobs, list):
        stats = calculate_statistics(JobListing.objects.filter(id__in=[j.id for j in jobs]))
        paginator = Paginator(jobs, 20)
    else:
        stats = calculate_statistics(jobs)
        paginator = Paginator(jobs, 20)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'job_list.html', {
        'jobs': page_obj,
        'stats': stats,
        'search_mode': search_mode,
    })


def job_detail(request, job_id):
    """Detailed view of a single job"""
    job = get_object_or_404(JobListing, id=job_id)
    return render(request, 'job_detail.html', {
        'job': job,
    })


def subscribe(request):
    """Subscribe to email alerts"""
    if request.method == 'POST':
        email = request.POST.get('email')
        job_types = request.POST.getlist('job_types')
        sectors = request.POST.getlist('sectors')
        zip_code = request.POST.get('zip_code', '')
        max_distance = request.POST.get('max_distance', '')
        
        try:
            subscriber, created = EmailSubscriber.objects.get_or_create(
                email=email,
                defaults={
                    'job_types': job_types,
                    'sectors': sectors,
                    'is_active': True,
                    'zip_code': zip_code,
                    'max_distance_miles': int(max_distance) if max_distance else None,
                }
            )
            
            if created:
                messages.success(request, f'🎉 Successfully subscribed! You will receive alerts at {email}')
            else:
                subscriber.job_types = job_types
                subscriber.sectors = sectors
                subscriber.is_active = True
                subscriber.zip_code = zip_code
                subscriber.max_distance_miles = int(max_distance) if max_distance else None
                subscriber.save()
                messages.success(request, f'✅ Subscription updated for {email}')
                
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    return render(request, 'subscribe.html')

from datetime import datetime, timedelta

def cleanup_old_jobs():
    """Auto-close jobs older than 60 days"""
    cutoff_date = datetime.now() - timedelta(days=60)
    old_jobs = JobListing.objects.filter(
        closed=False,
        date_scraped__lt=cutoff_date
    )
    count = old_jobs.update(closed=True)
    return count


def trigger_scrape(request):
    """Trigger manual scraping run using USAJobs API"""
    if request.method == 'POST':
        try:
            from .usajobs_scraper import USAJobsScraper
            
            # Initialize scraper with API key
            scraper = USAJobsScraper(
                api_key="3T5mKByJh7G2xfH+agJ+yj4ez6yTCgjJ0kZ8wVHrPds=",
                user_email="sawyer.mustopoh@gmail.com"
            )
            
            # ULTIMATE comprehensive public service keywords
            stats = scraper.scrape_multiple_keywords([
                # Core Public Service
                "public policy",
                "public administration",
                "public management",
                "public service",
                "public affairs",
                "government affairs",
                
                # Legislative & Congressional
                "legislative",
                "congressional",
                "policy analyst",
                "policy advisor",
                
                # Program Management
                "program analyst",
                "program manager",
                "program coordinator",
                "management analyst",
                "budget analyst",
                "grants management",
                
                # Public Health
                "public health",
                "health policy",
                "epidemiology",
                "community health",
                
                # Social Services
                "social services",
                "social work",
                "human services",
                "community development",
                "housing",
                
                # Education
                "education policy",
                "education program",
                
                # Environment & Energy
                "environmental policy",
                "climate",
                "sustainability",
                "energy policy",
                
                # Economic Development
                "economic development",
                "urban planning",
                "city planning",
                
                # International Affairs
                "international development",
                "foreign service",
                "diplomacy",
                "international relations",
                
                # Justice & Law
                "criminal justice",
                "legal",
                "regulatory",
                
                # Communications & Outreach
                "public information",
                "communications",
                "community outreach",
                "public relations",
                
                # Research & Evaluation
                "research analyst",
                "program evaluation",
                "data analyst",
                
                # Special Programs
                "presidential management fellowship",
                "pathways",
                "recent graduate program",
                "internship",
                "fellowship"
            ])
            
            # Auto-cleanup old jobs after scraping
            closed_count = cleanup_old_jobs()
            
            messages.success(
                request, 
                f'✅ Scraping completed! Found: {stats["found"]}, Added: {stats["created"]}. Auto-closed {closed_count} old jobs (60+ days).'
            )
        except Exception as e:
            messages.error(request, f'❌ Scraping failed: {str(e)}')
    
    return redirect('home')