
import pytest
from flask import Flask, render_template_string
from bs4 import BeautifulSoup
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def load_template():
    with open('src/templates/web_interface.html', 'r', encoding='utf-8') as f:
        return f.read()

def test_article_selection_ux_enhancements():
    app = Flask(__name__)

    # Define dummy routes used in template
    @app.route('/fetch')
    def fetch_articles(): pass

    @app.route('/save', methods=['POST'])
    def save_selection(): pass

    @app.route('/generate')
    def generate(): pass

    @app.route('/api/progress')
    def get_progress(): pass

    # Mock data
    data = {
        'total_articles': 1,
        'selected': [],
        'categories': {
            'news': [
                {
                    'id': '1',
                    'title': 'Test Article',
                    'url': 'http://example.com',
                    'source': 'Test Source',
                    'score': 10,
                    'summary': 'Summary',
                    'published': '2023-01-01',
                    'selected': False
                }
            ]
        }
    }

    template = load_template()

    with app.test_request_context():
        rendered_html = render_template_string(template, data=data)

    soup = BeautifulSoup(rendered_html, 'html.parser')

    # 1. Check for aria-label on checkbox
    checkbox = soup.find('input', {'type': 'checkbox'})
    assert checkbox is not None
    assert checkbox.has_attr('aria-label')
    assert checkbox['aria-label'] == 'Select article: Test Article'

    # 2. Check for onclick on article div
    article_div = soup.find('div', class_='article')
    assert article_div is not None
    assert article_div.has_attr('onclick')
    assert 'toggleArticle(this, event)' in article_div['onclick']

    # 3. Check for JS function definition
    script_content = soup.find_all('script')[-1].string # Assuming it's in the last script tag or combined
    # Actually, verify the function exists in any script tag
    found_function = False
    for script in soup.find_all('script'):
        if script.string and 'function toggleArticle(element, event)' in script.string:
            found_function = True
            break

    assert found_function, "toggleArticle function not found in script tags"

if __name__ == "__main__":
    # Manually run if executed directly
    try:
        test_article_selection_ux_enhancements()
        print("✅ Frontend structure verification passed!")
    except AssertionError as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
