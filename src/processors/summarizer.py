#!/usr/bin/env python3
"""
AI Summarization Module

Uses Google Gemini to generate article summaries and commentary.
"""

import os
from typing import List
import json

# Import from parent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from sources.rss_fetcher import Article

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Run: pip install google-generativeai")


def init_gemini(api_key: str = None):
    """Initialize Gemini with API key."""
    if not GEMINI_AVAILABLE:
        return False
        
    key = api_key or os.getenv('GEMINI_API_KEY')
    if not key:
        print("⚠️  GEMINI_API_KEY not set. Set it in environment or .env file")
        return False
        
    genai.configure(api_key=key)
    return True


def summarize_article(article: Article, config: dict) -> Article:
    """
    Generate AI summary and commentary for a single article.
    
    Args:
        article: Article to summarize
        config: Gemini configuration
        
    Returns:
        Article with ai_summary and ai_commentary populated
    """
    if not GEMINI_AVAILABLE:
        article.ai_summary = article.summary[:200] + "..."
        article.ai_commentary = ""
        return article
        
    model_name = config.get('model', 'gemini-1.5-flash')
    style = config.get('summary_style', 'analytical')
    include_commentary = config.get('include_commentary', True)
    max_length = config.get('max_summary_length', 150)
    
    # Build prompt based on style
    style_instructions = {
        'analytical': "Explain WHY this matters and its broader implications for the industry.",
        'brief': "Provide a concise, factual summary of the key points.",
        'detailed': "Provide a comprehensive, in-depth summary covering the full context, key findings, and implications."
    }
    
    prompt = f"""You are a senior technology analyst writing for "AI This Week", a professional newsletter for Canadian AI professionals, executives, and policymakers.

Article Title: {article.title}
Source: {article.source}
Category: {article.category or 'General'}
Original Content: {article.summary}

Your task is to write a detailed, insightful summary for newsletter readers.

REQUIREMENTS:
1. Write approximately {max_length} words - be thorough and substantive
2. {style_instructions.get(style, style_instructions['detailed'])}
3. Include:
   - The core news/development
   - Key details, data points, or quotes if available
   - Context: Why is this significant in the broader AI landscape?
   - Implications: What does this mean for businesses, professionals, or policymakers?
   - Canadian relevance if applicable
4. Write in a professional, analytical tone - not hype or marketing speak
5. Use clear, readable prose (not bullet points)

{"ALSO: Add a 'Commentary' section (2-3 sentences) with your analytical perspective on why this development matters and what readers should watch for." if include_commentary else ""}

Respond in JSON format:
{{
    "summary": "Your detailed summary here (approximately {max_length} words)...",
    "commentary": "Your analytical commentary here (2-3 sentences)..." 
}}
"""

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        # Parse JSON response
        response_text = response.text.strip()
        
        # Handle markdown code blocks
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        result = json.loads(response_text)
        
        article.ai_summary = result.get('summary', article.summary)
        article.ai_commentary = result.get('commentary', '')
        
    except json.JSONDecodeError:
        # If JSON parsing fails, use the raw response
        article.ai_summary = response.text[:500] if response else article.summary
        article.ai_commentary = ""
    except Exception as e:
        print(f"    ⚠️  Summarization error: {e}")
        article.ai_summary = article.summary[:300]
        article.ai_commentary = ""
        
    return article


def summarize_articles(articles: List[Article], config: dict, 
                       progress_callback=None) -> List[Article]:
    """
    Generate AI summaries for a list of articles.
    
    Args:
        articles: List of articles to summarize
        config: Full configuration dictionary
        progress_callback: Optional callback function for progress updates
        
    Returns:
        List of articles with AI summaries
    """
    gemini_config = config.get('gemini', {})
    
    if not init_gemini():
        print("⚠️  Gemini not available - using original summaries")
        return articles
        
    print(f"\n🤖 Generating AI summaries for {len(articles)} articles...")
    
    summarized = []
    for i, article in enumerate(articles, 1):
        print(f"  [{i}/{len(articles)}] {article.title[:50]}...")
        
        summarized_article = summarize_article(article, gemini_config)
        summarized.append(summarized_article)
        
        if progress_callback:
            progress_callback(i, len(articles))
            
    print("  ✓ Summarization complete")
    
    return summarized


def generate_deep_dive_topic(articles: List[Article], config: dict) -> dict:
    """
    Analyze top articles to suggest a deep dive topic.
    
    Returns:
        Dictionary with topic suggestion and reasoning
    """
    if not GEMINI_AVAILABLE or not init_gemini():
        return {"topic": "AI Governance", "reasoning": "Default suggestion"}
        
    # Get top 5 articles for analysis
    top_articles = articles[:5]
    articles_text = "\n".join([
        f"- {a.title} ({a.category})" for a in top_articles
    ])
    
    prompt = f"""Based on these top AI news articles this week, suggest ONE topic for a "Deep Dive" section in an AI newsletter:

{articles_text}

The deep dive should:
1. Be relevant to Canadian AI professionals
2. Connect multiple themes from the week's news
3. Provide lasting value beyond the news cycle

Respond in JSON:
{{
    "topic": "Suggested topic title",
    "reasoning": "Why this topic matters now",
    "key_questions": ["Question 1", "Question 2", "Question 3"]
}}
"""

    try:
        model = genai.GenerativeModel(config.get('gemini', {}).get('model', 'gemini-1.5-flash'))
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
                
        return json.loads(response_text)
        
    except Exception as e:
        print(f"⚠️  Deep dive suggestion error: {e}")
        return {"topic": "AI Governance Trends", "reasoning": "Default suggestion"}
