# AI Newsletter Bot

An automated tool for discovering, curating, and formatting AI-related articles for a weekly newsletter.

## Features

- **Article Discovery**: Automatically finds articles from configured sources (RSS feeds, news APIs, web scraping)
- **Topic Filtering**: Filters articles based on your areas of interest
- **AI Summarization**: Uses LLMs to create concise article summaries
- **Email Formatting**: Generates Outlook-ready HTML emails

## Project Structure

```
AI-newsletter-bot/
├── src/
│   ├── sources/          # Article source configurations
│   ├── scrapers/         # Web scraping modules
│   ├── processors/       # AI/LLM processing for summaries
│   └── formatters/       # Email HTML formatting
├── templates/            # Outlook-ready email templates
├── config/               # Configuration files
├── output/               # Generated newsletter drafts
├── requirements.txt
└── README.md
```

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Configure your sources in `config/sources.yaml`
6. Run: `python src/main.py`

## Configuration

Edit `config/sources.yaml` to add your article sources and topics of interest.

## Usage

```bash
# Generate this week's newsletter
python src/main.py

# Output will be saved to output/newsletter_YYYY-MM-DD.html
```

## License

Private - All rights reserved
