# PolicyPulse - A Job Scraper Django Project

A comprehensive job scraper for .gov, .edu, and .net domains with distance-based search, skill extraction, and email notifications.

## Features
- 🎯 Distance-based local job search
- 🌎 Nationwide search with advanced filters
- 📊 Real-time statistics on skills and sectors
- 📧 Email notifications for new jobs
- 💼 Automatic job scraping from multiple sources

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create database:
```bash
createdb job_scraper_db
```

3. Configure `.env` file with your credentials

4. Run migrations:
```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Run server:
```bash
python manage.py runserver
```

Visit http://localhost:8000/

## Usage

- **Local Search**: Enter zip code and distance to find nearby jobs
- **Nationwide Search**: Browse all jobs with filters
- **Statistics**: View skill demand and sector distribution
- **Subscribe**: Get email alerts for new postings
- **Admin Panel**: Manage jobs at /admin/