
from flask import Flask, render_template_string, jsonify
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

app = Flask(__name__)

# Load template
template_path = Path(__file__).parent.parent / "src" / "templates" / "web_interface.html"
with open(template_path, 'r', encoding='utf-8') as f:
    template_content = f.read()

@app.route('/')
def index():
    mock_data = {
        "total_articles": 2,
        "selected": [],
        "categories": {
            "news": [
                {
                    "id": "1",
                    "title": "Article One",
                    "url": "#",
                    "source": "Source A",
                    "score": 9.0,
                    "summary": "Summary A",
                    "published": "2023-10-27",
                    "selected": False
                },
                {
                    "id": "2",
                    "title": "Article Two",
                    "url": "#",
                    "source": "Source B",
                    "score": 8.0,
                    "summary": "Summary B",
                    "published": "2023-10-27",
                    "selected": False
                }
            ]
        }
    }
    return render_template_string(template_content, data=mock_data)

@app.route('/fetch')
def fetch_articles(): return 'Fetch'

@app.route('/save', methods=['POST'])
def save_selection(): return jsonify({"status": "ok"})

@app.route('/generate')
def generate(): return 'Generate'

@app.route('/api/progress')
def get_progress(): return jsonify({"status": "idle"})

if __name__ == '__main__':
    app.run(port=5001)
