import requests
from datetime import datetime
from .models import JobListing, ScrapingLog
import time


class USAJobsScraper:
    """
    Real scraper using USAJobs official API
    Get your free API key at: https://developer.usajobs.gov/APIRequest/Index
    """
    
    def __init__(self, api_key, user_email):
        self.api_key = api_key
        self.user_email = user_email
        self.base_url = "https://data.usajobs.gov/api/search"
        
        self.headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": user_email,
            "Authorization-Key": api_key
        }
    
    def determine_job_type(self, title, description):
        """Determine if it's an internship, fellowship, or job - STRICT matching"""
        title_lower = title.lower()
        description_lower = description.lower()
        
        # STRICT: Must explicitly say "internship" or "intern" in title or first 200 chars
        internship_keywords = ["internship", "intern program", "student trainee", "pathways intern"]
        if any(keyword in title_lower for keyword in internship_keywords):
            return "internship"
        
        # Check description only if very explicit
        description_start = description_lower[:200]
        if "internship program" in description_start or "intern position" in description_start:
            return "internship"
        
        # STRICT: Must explicitly say "fellowship" in title or first 200 chars
        fellowship_keywords = ["fellowship", "presidential management fellow"]
        if any(keyword in title_lower for keyword in fellowship_keywords):
            return "fellowship"
        
        if "fellowship program" in description_start:
            return "fellowship"
        
        # DEFAULT: Everything else is a job
        return "job"
    
    def extract_skills(self, text):
        """Extract technical and soft skills - MASSIVELY EXPANDED"""
        text_lower = text.lower()
        
        technical_skills = {
            "Programming Languages": [],
            "Data Science & Analytics": [],
            "Cloud & DevOps": [],
            "Security & Compliance": [],
            "Office & Productivity": [],
            "Research & Analysis": [],
            "Design & Creative": [],
            "Project Management": [],
            "Financial & Budget": []
        }
        
        soft_skills = []
        
        # EXPANDED Programming Languages
        prog_langs = [
            "python", "java", "javascript", "typescript", "c++", "c#", "ruby", 
            "go", "rust", "swift", "kotlin", "php", "r", "matlab", "scala",
            "sql", "nosql", "html", "css", "perl", "vba", "shell scripting",
            "bash", "powershell", "sas", "spss", "stata"
        ]
        for lang in prog_langs:
            if lang in text_lower:
                technical_skills["Programming Languages"].append(lang.upper() if len(lang) <= 4 else lang.title())
        
        # EXPANDED Data Science & Analytics
        data_skills = [
            "machine learning", "deep learning", "ai", "artificial intelligence",
            "data analysis", "data analytics", "statistics", "statistical analysis",
            "data visualization", "tableau", "power bi", "excel", "data mining",
            "predictive modeling", "quantitative analysis", "regression", "modeling",
            "big data", "hadoop", "spark", "pandas", "numpy", "scikit-learn",
            "tensorflow", "pytorch", "neural networks", "nlp", "natural language processing",
            "data warehousing", "etl", "business intelligence", "reporting",
            "dashboards", "metrics", "kpi", "analytics"
        ]
        for skill in data_skills:
            if skill in text_lower:
                technical_skills["Data Science & Analytics"].append(skill.title())
        
        # EXPANDED Cloud & DevOps
        cloud_skills = [
            "aws", "azure", "gcp", "google cloud", "cloud computing",
            "docker", "kubernetes", "ci/cd", "jenkins", "devops",
            "terraform", "ansible", "linux", "unix", "bash",
            "containerization", "microservices", "serverless",
            "infrastructure as code", "automation", "monitoring",
            "grafana", "prometheus", "elastic", "deployment"
        ]
        for skill in cloud_skills:
            if skill in text_lower:
                technical_skills["Cloud & DevOps"].append(skill.upper() if skill in ["aws", "gcp"] else skill.title())
        
        # EXPANDED Security & Compliance
        security_skills = [
            "cybersecurity", "information security", "infosec",
            "penetration testing", "encryption", "security clearance",
            "vulnerability", "risk assessment", "compliance", "fisma",
            "nist", "fedramp", "iso 27001", "hipaa", "gdpr",
            "security operations", "incident response", "threat analysis",
            "firewall", "ids", "ips", "siem", "authentication",
            "authorization", "access control"
        ]
        for skill in security_skills:
            if skill in text_lower:
                technical_skills["Security & Compliance"].append(skill.upper() if len(skill) <= 5 else skill.title())
        
        # EXPANDED Office & Productivity
        office_skills = [
            "microsoft office", "excel", "word", "powerpoint", "outlook",
            "sharepoint", "google workspace", "microsoft teams", "slack",
            "office 365", "g suite", "onedrive", "google docs",
            "google sheets", "access", "visio", "project"
        ]
        for skill in office_skills:
            if skill in text_lower:
                technical_skills["Office & Productivity"].append(skill.title())
        
        # EXPANDED Research & Analysis
        research_skills = [
            "research", "policy analysis", "program evaluation", 
            "qualitative analysis", "quantitative research", "survey design",
            "grant writing", "budget analysis", "cost-benefit analysis",
            "strategic planning", "feasibility study", "impact assessment",
            "literature review", "case study", "needs assessment",
            "data collection", "field research", "archival research"
        ]
        for skill in research_skills:
            if skill in text_lower:
                technical_skills["Research & Analysis"].append(skill.title())
        
        # NEW: Design & Creative
        design_skills = [
            "graphic design", "ui/ux", "user experience", "user interface",
            "adobe creative suite", "photoshop", "illustrator", "indesign",
            "figma", "sketch", "wireframing", "prototyping",
            "web design", "visual design", "branding", "typography",
            "video editing", "premiere", "final cut"
        ]
        for skill in design_skills:
            if skill in text_lower:
                technical_skills["Design & Creative"].append(skill.title())
        
        # NEW: Project Management
        pm_skills = [
            "project management", "agile", "scrum", "kanban", "waterfall",
            "pmp", "prince2", "jira", "trello", "asana", "monday.com",
            "gantt chart", "risk management", "stakeholder management",
            "change management", "process improvement", "six sigma",
            "lean", "sprint planning", "backlog management"
        ]
        for skill in pm_skills:
            if skill in text_lower:
                technical_skills["Project Management"].append(skill.upper() if skill == "pmp" else skill.title())
        
        # NEW: Financial & Budget
        financial_skills = [
            "budget", "budgeting", "financial analysis", "financial management",
            "cost analysis", "forecasting", "accounting", "bookkeeping",
            "financial reporting", "accounts payable", "accounts receivable",
            "procurement", "contract management", "grants management",
            "fiscal management", "appropriations", "obligations"
        ]
        for skill in financial_skills:
            if skill in text_lower:
                technical_skills["Financial & Budget"].append(skill.title())
        
        # Remove empty categories and duplicates
        technical_skills = {k: list(set(v)) for k, v in technical_skills.items() if v}
        
        # MASSIVELY EXPANDED Soft Skills
        soft_skill_keywords = [
            # Communication
            "communication", "written communication", "verbal communication",
            "oral communication", "interpersonal communication",
            "presentation skills", "public speaking", "briefing",
            
            # Collaboration
            "teamwork", "collaboration", "team player", "cross-functional",
            "stakeholder engagement", "relationship building",
            
            # Leadership
            "leadership", "management", "supervision", "mentoring",
            "coaching", "delegation", "team building",
            
            # Analytical
            "problem solving", "critical thinking", "analytical thinking",
            "analytical skills", "decision making", "judgment",
            
            # Attention to Detail
            "attention to detail", "detail oriented", "accuracy",
            "thoroughness", "precision",
            
            # Organization
            "time management", "organizational skills", "multitasking",
            "prioritization", "planning", "scheduling",
            
            # Interpersonal
            "interpersonal skills", "customer service", "client relations",
            "stakeholder relations", "diplomacy", "tact",
            
            # Adaptability
            "adaptability", "flexibility", "agility", "resilience",
            "change management", "problem resolution",
            
            # Initiative
            "initiative", "self-motivated", "independent", "proactive",
            "self-starter", "autonomous",
            
            # Work Ethic
            "work ethic", "reliability", "dependability", "commitment",
            "dedication", "professionalism",
            
            # Creativity
            "creativity", "innovation", "creative thinking", "problem solving",
            
            # Other Important
            "conflict resolution", "negotiation", "persuasion",
            "cultural competency", "emotional intelligence"
        ]
        
        for skill in soft_skill_keywords:
            if skill in text_lower:
                soft_skills.append(skill.title())
        
        # Remove duplicates
        soft_skills = list(set(soft_skills))
        
        return technical_skills, soft_skills
    
    def identify_sectors(self, org_name, description):
        """Identify job sectors"""
        combined = (org_name + " " + description).lower()
        sectors = []
        
        sector_keywords = {
            "Government": ["federal", "government", "agency", "department"],
            "Technology": ["technology", "it", "software", "digital"],
            "Healthcare": ["health", "medical", "cdc", "nih"],
            "Science": ["science", "research", "nasa", "laboratory"],
            "Defense": ["defense", "military", "homeland", "intelligence"],
            "Education": ["education", "student", "academic"]
        }
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in combined for keyword in keywords):
                sectors.append(sector)
        
        return sectors if sectors else ["Government"]
    
    def parse_job(self, job_item):
        """Parse a single job from USAJobs API response"""
        try:
            job = job_item['MatchedObjectDescriptor']
            
            # Basic info
            title = job.get('PositionTitle', '')
            apply_link = job.get('PositionURI', '')
            org_name = job.get('OrganizationName', 'Federal Government')
            
            # Location - FIXED for encoding issues
            locations = []
            if 'PositionLocation' in job and job['PositionLocation']:
                for loc in job['PositionLocation']:
                    city = loc.get('CityName', '')
                    state = loc.get('CountrySubDivisionCode', '')
                    # Clean up city name
                    if city:
                        city = str(city).split(',')[0].strip()
                    if city and state:
                        locations.append(f"{city}, {state}")
            
            # Fallback to PositionLocationDisplay
            if not locations:
                location_display = job.get('PositionLocationDisplay', 'Location TBD')
                if isinstance(location_display, list):
                    locations = [str(loc).strip() for loc in location_display if loc]
                else:
                    locations = [str(location_display).strip()]
            
            # Work format (federal jobs are typically onsite)
            work_format = ["onsite"]
            
            # Get full description
            job_summary = job.get('UserArea', {}).get('Details', {}).get('JobSummary', '')
            major_duties = job.get('UserArea', {}).get('Details', {}).get('MajorDuties', '')
            
            # Make sure they're strings, not lists
            if isinstance(job_summary, list):
                job_summary = ' '.join(str(s) for s in job_summary)
            if isinstance(major_duties, list):
                major_duties = ' '.join(str(d) for d in major_duties)
                
            description = str(job_summary) + " " + str(major_duties)
            
            # Determine job type - STRICT
            job_type = self.determine_job_type(title, description)
            
            # Extract skills - EXPANDED
            technical_skills, soft_skills = self.extract_skills(description)
            
            # Identify sectors
            sectors = self.identify_sectors(org_name, description)
            
            # Dates
            posting_date = job.get('PublicationStartDate', '')
            if posting_date:
                posting_date = posting_date.split('T')[0]
            
            return {
                "title": title,
                "job_type": job_type,
                "organization": org_name,
                "apply_link": apply_link,
                "locations": locations,
                "work_format": work_format,
                "sectors": sectors,
                "technical_skills": technical_skills,
                "soft_skills": soft_skills,
                "posting_date": posting_date,
                "source_domain": "usajobs.gov",
            }
            
        except Exception as e:
            print(f"    ⚠️ Error parsing job: {e}")
            return None
    
    def search_jobs(self, keyword="internship", results_per_page=100, max_pages=2):
        """Search for jobs on USAJobs"""
        all_jobs = []
        
        for page in range(1, max_pages + 1):
            print(f"\nFetching page {page} for keyword: '{keyword}'")
            
            params = {
                "Keyword": keyword,
                "ResultsPerPage": results_per_page,
                "Page": page,
                "Fields": "Full"
            }
            
            try:
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
                
                search_result = data.get('SearchResult', {})
                total_jobs = search_result.get('SearchResultCountAll', 0)
                jobs_this_page = search_result.get('SearchResultCount', 0)
                
                print(f"  Total matching jobs: {total_jobs}")
                print(f"  Jobs on this page: {jobs_this_page}")
                
                if jobs_this_page == 0:
                    break
                
                job_items = search_result.get('SearchResultItems', [])
                
                for job_item in job_items:
                    parsed_job = self.parse_job(job_item)
                    if parsed_job:
                        all_jobs.append(parsed_job)
                
                if len(all_jobs) >= total_jobs:
                    break
                
                if page < max_pages:
                    time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                print(f"  API request failed: {e}")
                break
        
        return all_jobs
    
    def save_jobs(self, jobs):
        """Save jobs to database"""
        stats = {"created": 0, "skipped": 0}
        
        for job_data in jobs:
            try:
                existing = JobListing.objects.filter(
                    apply_link=job_data['apply_link']
                ).first()
                
                if existing:
                    stats['skipped'] += 1
                else:
                    JobListing.objects.create(**job_data)
                    stats['created'] += 1
                    print(f"  ✅ Created: {job_data['title'][:60]}...")
                    
            except Exception as e:
                print(f"  ❌ Error saving job: {e}")
        
        return stats
    
    def scrape_multiple_keywords(self, keywords=None):
        """Scrape jobs for multiple keywords"""
        if keywords is None:
            keywords = ["internship", "fellowship"]
        
        log = ScrapingLog.objects.create(
            status='running',
            sites_scraped=[f"USAJobs: {kw}" for kw in keywords]
        )
        
        all_jobs = []
        
        try:
            for keyword in keywords:
                print(f"\n{'='*60}")
                print(f"SEARCHING FOR: {keyword.upper()}")
                print(f"{'='*60}")
                
                jobs = self.search_jobs(keyword=keyword, results_per_page=100, max_pages=2)
                all_jobs.extend(jobs)
                
                print(f"\n  Found {len(jobs)} jobs for '{keyword}'")
                
                if keyword != keywords[-1]:
                    time.sleep(3)
            
            print(f"\n\nSAVING JOBS TO DATABASE")
            
            stats = self.save_jobs(all_jobs)
            
            log.status = 'completed'
            log.jobs_found = len(all_jobs)
            log.jobs_added = stats['created']
            log.completed_at = datetime.now()
            log.save()
            
            print(f"\n{'='*60}")
            print(f"SCRAPING COMPLETE!")
            print(f"Total Found: {len(all_jobs)}")
            print(f"Created: {stats['created']}")
            print(f"Skipped: {stats['skipped']}")
            print(f"{'='*60}\n")
            
            return {
                'found': len(all_jobs),
                'created': stats['created'],
                'updated': 0
            }
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.completed_at = datetime.now()
            log.save()
            raise