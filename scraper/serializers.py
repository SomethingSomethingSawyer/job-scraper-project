from rest_framework import serializers
from .models import JobListing, EmailSubscriber, ScrapingLog


class JobListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobListing
        fields = '__all__'
        read_only_fields = ['date_scraped', 'date_updated']


class JobListingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating jobs with validation"""
    class Meta:
        model = JobListing
        fields = [
            'title', 'job_type', 'organization', 'company_link', 'company_logo',
            'locations', 'work_format', 'technical_skills', 'soft_skills',
            'sectors', 'apply_link', 'source_domain', 'closed',
            'sponsorship_required', 'posting_date', 'zip_codes',
            'latitude', 'longitude'
        ]


class EmailSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSubscriber
        fields = ['email', 'job_types', 'sectors', 'is_active', 'zip_code', 'max_distance_miles']


class ScrapingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingLog
        fields = '__all__'