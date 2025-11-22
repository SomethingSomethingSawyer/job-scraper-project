from django.test import TestCase
from .models import JobListing, EmailSubscriber

class JobListingTestCase(TestCase):
    def setUp(self):
        JobListing.objects.create(
            title="Software Engineering Intern",
            job_type="internship",
            organization="Test Company",
            apply_link="https://example.com/apply"
        )
    
    def test_job_creation(self):
        """Test that a job can be created"""
        job = JobListing.objects.get(title="Software Engineering Intern")
        self.assertEqual(job.job_type, "internship")
        self.assertEqual(job.organization, "Test Company")