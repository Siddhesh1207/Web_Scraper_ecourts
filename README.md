# ⚖️ New Delhi District Court Cause List Scraper

A decoupled, full-stack web scraping application designed to automate the extraction of daily cause lists from the New Delhi District Court website and generate cleanly formatted PDFs. 

**Target URL:** [https://newdelhi.dcourts.gov.in/cause-list-⁄-daily-board/](https://newdelhi.dcourts.gov.in/cause-list-%e2%81%84-daily-board/)

## 🚀 Features
* **Decoupled Architecture:** Lightning-fast static HTML/JS frontend powered by a robust Python/FastAPI backend.
* **Automated Batch Processing:** Users can queue multiple courts within a complex. The orchestrator systematically loads the required CAPTCHAs, processes the downloads, and seamlessly loops to the next court.
* **Advanced Bot-Evasion:** Utilizes `undetected_chromedriver` to safely navigate government bot-protection mechanisms.
* **Automated PDF Generation:** Scraped HTML tables are dynamically parsed and converted into styled, readable PDFs using `reportlab`.
* **Memory Management:** Includes a background asynchronous task manager to cleanly kill abandoned headless browser sessions, preventing memory leaks in containerized environments.

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Netlify-ready)
* **Backend:** Python 3.11+, FastAPI, Uvicorn
* **Scraping Engine:** Selenium WebDriver, `undetected_chromedriver`, BeautifulSoup4
* **Infrastructure:** Docker, Xvfb (Virtual Framebuffer for headless Chrome)

## ⚠️ Important Deployment Note: Government Geo-Blocking
The target domain (`.gov.in`) is protected by National Informatics Centre (NIC) firewalls that employ strict network-level geo-blocking. 
* **The Challenge:** Traffic originating from foreign data centers (such as standard free tiers on Hugging Face, Render, or Heroku in the US/EU) will have their connections silently dropped (Timeout Errors). 
* **The Solution:** To run this application in a production environment, the Docker container **must be deployed to a server with an Indian IP address** (e.g., AWS EC2 `ap-south-1` Mumbai region or an Indian VPS). For local testing, running the app from a local Indian network works perfectly.

## 💻 Local Setup & Installation

### Option 1: Running via Docker (Recommended)
Make sure you have Docker installed on your machine.

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/delhi-court-scraper.git](https://github.com/YOUR_USERNAME/delhi-court-scraper.git)
   cd delhi-court-scraper
