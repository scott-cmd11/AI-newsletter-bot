# 🤖 AI Newsletter Bot

**Automate your weekly AI newsletter curation with smart article discovery and AI-powered summaries.**

---

## 📍 Project Location

```
C:\Users\scott\.gemini\antigravity\scratch\AI-newsletter-bot
```

**Quick Access Tip:** Pin this folder to Quick Access in File Explorer, or create a desktop shortcut.

---

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)

1. **Open PowerShell** and run:
   ```powershell
   cd C:\Users\scott\.gemini\antigravity\scratch\AI-newsletter-bot
   .\venv\Scripts\Activate
   $env:GEMINI_API_KEY='AIzaSyBk0Xo4Awbsje-ku3v-MN1ICS7hY7fsC1E'
   python src/web.py
   ```

2. **Browser opens automatically** at http://127.0.0.1:5000

3. **Select articles** → Click **Generate Newsletter** → Copy to Outlook

### Option 2: Command Line

```powershell
cd C:\Users\scott\.gemini\antigravity\scratch\AI-newsletter-bot
.\venv\Scripts\Activate
$env:GEMINI_API_KEY='AIzaSyBk0Xo4Awbsje-ku3v-MN1ICS7hY7fsC1E'

# Step 1: Fetch articles
python src/cli.py scout

# Step 2: Select articles interactively
python src/cli.py curate

# Step 3: Generate newsletter
python src/cli.py compose --preview
```

---

## 📂 Project Structure

```
AI-newsletter-bot/
├── config/
│   └── sources.yaml     # RSS feeds, topics, and settings
├── src/
│   ├── web.py           # Web interface
│   ├── cli.py           # Command-line interface
│   ├── sources/         # Article fetching
│   ├── processors/      # Scoring & AI summaries
│   └── formatters/      # Email HTML generation
├── output/              # Generated newsletters
└── run_scout.bat        # Scheduled automation script
```

---

## ⚙️ Configuration

Edit `config/sources.yaml` to:
- Add/remove Google Alerts RSS feeds
- Adjust topic keywords and priorities
- Customize your writing style
- Enable/disable Theme of the Week

---

## 📅 Automated Overnight Fetching

To have articles ready every morning:

1. Open **Task Scheduler** (Windows search)
2. Click **Create Basic Task**
3. Name: `AI Newsletter Scout`
4. Trigger: **Daily** at **11:00 PM**
5. Action: **Start a program**
6. Program: `C:\Users\scott\.gemini\antigravity\scratch\AI-newsletter-bot\run_scout.bat`

---

## 🔑 Your Gemini API Key

```
AIzaSyBk0Xo4Awbsje-ku3v-MN1ICS7hY7fsC1E
```

This is your free Gemini API key. Keep it private.

---

## 📧 Weekly Workflow

**Every Thursday:**
1. Open web interface: `python src/web.py`
2. Click "Refresh Articles" if needed
3. Select 6-8 articles across categories
4. Click "Generate Newsletter"
5. Copy HTML to Outlook → Send Friday!

---

## 🛠️ Troubleshooting

**"No articles loaded"** → Click "Fetch New Articles"

**API errors** → Check that GEMINI_API_KEY is set

**Port 5000 in use** → Close other web servers or change port in web.py

---

## 📦 GitHub Repository

Private repo: https://github.com/scott-cmd11/AI-newsletter-bot

---

*Built with ❤️ for AI This Week*
