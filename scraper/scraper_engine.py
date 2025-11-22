import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
from urllib.parse import urljoin, urlparse
from .models import JobListing, ScrapingLog
from .serializers import JobListingCreateSerializer


class UniversalJobScraper:
    """Advanced scraper that integrates with Django models"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        self.job_type_keywords = {
            "internship": ["intern", "internship", "summer program", "co-op"],
            "job": ["full-time", "full time", "permanent", "career", "position"],
            "fellowship": ["fellowship", "fellow", "postdoc", "post-doctoral"]
        }
        
        self.technical_skills = {
            "Programming Languages": [
                "python", "java", "javascript", "typescript", "c++", "c#", "ruby", 
                "go", "rust", "swift", "kotlin", "php", "r", "matlab", "scala"
            ],
            "Web Development": [
                "react", "angular", "vue", "node.js", "django", "flask", "spring",
                "html", "css", "rest api", "graphql", "webpack"
            ],
            "Data Science": [
                "machine learning", "deep learning", "neural networks", "nlp",
                "computer vision", "data analysis", "statistics", "sql", "nosql",
                "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch"
            ],
            "Cloud & DevOps": [
                "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins",
                "terraform", "ansible", "linux", "unix", "bash"
            ],
            "Security": [
                "cybersecurity", "penetration testing", "encryption", "authentication",
                "security clearance", "firewall", "vulnerability"
            ],
            "Design": [
                "ui/ux", "figma", "sketch", "adobe", "photoshop", "illustrator"
            ]
        }
        
        self.soft_skills = [
            "communication", "teamwork", "leadership", "problem solving",
            "analytical", "critical thinking", "collaboration", "presentation",
            "writing", "research", "project management", "agile", "scrum"
        ]
        
        self.sectors = {
            "Technology": ["software", "it", "tech", "digital", "computing"],
            "Healthcare": ["health", "medical", "clinical", "hospital", "patient"],
            "Finance": ["finance", "banking", "investment", "trading", "fintech"],
            "Government": ["government", "federal", "state", "public sector", "policy"],
            "Education": ["education", "academic", "teaching", "research", "university"],
            "Energy": ["energy", "renewable", "utilities", "power", "environmental"],
            "Defense": ["defense", "military", "national security", "intelligence"],
            "Science": ["research", "laboratory", "scientific", "engineering"]
        }
        
        self.work_formats = {
            "remote": ["remote", "work from home", "wfh", "virtual", "telecommute"],
            "hybrid": ["hybrid", "flexible", "mix of remote"],
            "onsite": ["on-site", "onsite", "in-person", "office-based"]
        }
        
        self.job_listing_patterns = [
            {'tag': 'div', 'class_pattern': r'job[-_]?(listing|card|item|post)'},
            {'tag': 'li', 'class_pattern': r'job[-_]?(listing|card|item|post)'},
            {'tag': 'tr', 'class_pattern': r'job[-_]?row'},
            {'tag': 'article', 'class_pattern': r'(job|position|vacancy)'},
            {'tag': 'li', 'class_pattern': r'usajobs'},
            {'tag': 'div', 'class_pattern': r'(career|position)[-_]?posting'},
        ]
    
    def extract_locations(self, text):
        """Extract location information from text."""
        locations = []
        city_state = r'([A-Za-z\s]+),\s*([A-Z]{2})'
        matches = re.findall(city_state, text)
        for city, state in matches:
            locations.append(f"{city.strip()}, {state}")
        
        if re.search(r'\bremote\b', text, re.IGNORECASE):
            locations.append("Remote")
        if re.search(r'\bhybrid\b', text, re.IGNORECASE):
            locations.append("Hybrid")
        
        return list(set(locations)) if locations else ["Location Not Specified"]
    
    def determine_work_format(self, text):
        """Determine work format."""
        text_lower = text.lower()
        formats = []
        
        for format_type, keywords in self.work_formats.items():
            if any(keyword in text_lower for keyword in keywords):
                formats.append(format_type)
        
        return formats if formats else ["onsite"]
    
    def extract_skills(self, text):
        """Extract skills from text."""
        text_lower = text.lower()
        found_skills = {
            "technical": {},
            "soft": []
        }
        
        for category, skills in self.technical_skills.items():
            category_skills = []
            for skill in skills:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    category_skills.append(skill.title())
            if category_skills:
                found_skills["technical"][category] = category_skills
        
        for skill in self.soft_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills["soft"].append(skill.title())
        
        return found_skills
    
    def identify_sectors(self, text):
        """Identify sectors."""
        text_lower = text.lower()
        identified_sectors = []
        
        for sector, keywords in self.sectors.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_sectors.append(sector)
        
        return identified_sectors if identified_sectors else ["General"]
    
    def determine_job_type(self, title, description):
        """Determine job type."""
        combined_text = (title + " " + description).lower()
        
        for job_type, keywords in self.job_type_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return job_type
        
        return "job"
    
    def extract_organization(self, url):
        """Extract organization name from URL."""
        domain = urlparse(url).netloc
        org = domain.replace('www.', '').split('.')[0]
        return org.title()
    
    def fetch_job_description(self, url, timeout=5):
        """Fetch full job description."""
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            desc_patterns = [
                {'tag': 'div', 'class_pattern': r'(description|details|content)'},
                {'tag': 'section', 'class_pattern': r'(description|details|content)'},
            ]
            
            for pattern in desc_patterns:
                desc_elem = soup.find(pattern['tag'], class_=re.compile(pattern['class_pattern'], re.I))
                if desc_elem:
                    return desc_elem.get_text(separator=' ', strip=True)
            
            main = soup.find('main') or soup.find('body')
            if main:
                return main.get_text(separator=' ', strip=True)[:5000]
            
        except Exception as e:
            print(f"Could not fetch description: {e}")
        
        return ""
    
    def extract_job_details(self, card, base_url):
        """Extract job details and return data dict."""
        try:
            title_elem = (
                card.find('a', class_=re.compile(r'job[-_]?title', re.I)) or
                card.find(['h2', 'h3', 'h4']) or
                card.find('a')
            )
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            if title_elem.name == 'a':
                link = title_elem.get('href', '')
            else:
                link_elem = card.find('a')
                link = link_elem.get('href', '') if link_elem else ''
            
            if link and not link.startswith('http'):
                link = urljoin(base_url, link)
            
            if not link:
                return None
            
            card_text = card.get_text(separator=' ', strip=True)
            description = self.fetch_job_description(link)
            if not description:
                description = card_text
            
            locations = self.extract_locations(card_text)
            work_format = self.determine_work_format(description)
            skills = self.extract_skills(description)
            sectors = self.identify_sectors(description)
            job_type = self.determine_job_type(title, description)
            
            date_elem = card.find(text=re.compile(r'\d{1,2}/\d{1,2}/\d{2,4}'))
            posting_date = date_elem.strip() if date_elem else ""
            
            return {
                "title": title,
                "job_type": job_type,
                "organization": self.extract_organization(base_url),
                "apply_link": link,
                "locations": locations,
                "work_format": work_format,
                "sectors": sectors,
                "technical_skills": skills["technical"],
                "soft_skills": skills["soft"],
                "posting_date": posting_date,
                "source_domain": urlparse(base_url).netloc,
            }
            
        except Exception as e:
            print(f"Error parsing job: {e}")
            return None
    
    def find_job_listings(self, soup, base_url):
        """Find job listing elements."""
        for pattern in self.job_listing_patterns:
            cards = soup.find_all(
                pattern['tag'],
                class_=re.compile(pattern['class_pattern'], re.I)
            )
            if cards:
                print(f"  Found {len(cards)} listings")
                return cards
        
        job_links = soup.find_all('a', href=re.compile(r'(job|career|position)', re.I))
        filtered = [link for link in job_links if len(link.get_text(strip=True)) > 10]
        
        if filtered:
            print(f"  Found {len(filtered)} job links")
            return filtered
        
        return []
    
    def save_or_update_job(self, job_data):
        """Save new job or update existing one."""
        existing_job = JobListing.objects.filter(apply_link=job_data['apply_link']).first()
        
        if existing_job:
            updated = False
            if existing_job.closed != job_data.get('closed', False):
                existing_job.closed = job_data.get('closed', False)
                updated = True
            
            if updated:
                existing_job.save()
                return 'updated'
            return 'unchanged'
        else:
            serializer = JobListingCreateSerializer(data=job_data)
            if serializer.is_valid():
                serializer.save()
                return 'created'
            else:
                print(f"Validation error: {serializer.errors}")
                return 'error'
    
    def scrape_site(self, url, log=None):
        """Scrape a single site."""
        print(f"\nScraping: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            cards = self.find_job_listings(soup, url)
            
            if not cards:
                print("  No listings found")
                return {'found': 0, 'created': 0, 'updated': 0}
            
            stats = {'found': 0, 'created': 0, 'updated': 0}
            
            for i, card in enumerate(cards[:100]):
                job_data = self.extract_job_details(card, url)
                if job_data:
                    stats['found'] += 1
                    result = self.save_or_update_job(job_data)
                    if result == 'created':
                        stats['created'] += 1
                    elif result == 'updated':
                        stats['updated'] += 1
                
                if i > 0 and i % 10 == 0:
                    time.sleep(1)
            
            print(f"  ✅ Found: {stats['found']}, Created: {stats['created']}, Updated: {stats['updated']}")
            return stats
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {'found': 0, 'created': 0, 'updated': 0, 'error': str(e)}
    
    def scrape_multiple_sites(self, urls):
        """Scrape multiple sites with logging."""
        log = ScrapingLog.objects.create(
            status='running',
            sites_scraped=urls
        )
        
        total_stats = {'found': 0, 'created': 0, 'updated': 0}
        
        try:
            for url in urls:
                stats = self.scrape_site(url, log)
                total_stats['found'] += stats.get('found', 0)
                total_stats['created'] += stats.get('created', 0)
                total_stats['updated'] += stats.get('updated', 0)
                time.sleep(2)
            
            log.status = 'completed'
            log.jobs_found = total_stats['found']
            log.jobs_added = total_stats['created']
            log.jobs_updated = total_stats['updated']
            log.completed_at = datetime.now()
            log.save()
            
            return total_stats
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.completed_at = datetime.now()
            log.save()
            raise