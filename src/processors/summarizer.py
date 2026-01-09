#!/usr/bin/env python3
"""
AI Summarization Module

Uses Google Gemini to generate article summaries and commentary.
"""

import os
import logging
from typing import List
import json
import asyncio

# Import from parent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from sources.rss_fetcher import Article

logger = logging.getLogger(__name__)

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Run: pip install google-generativeai")


def init_gemini(api_key: str = None) -> bool:
    """Initialize Gemini with API key."""
    if not GEMINI_AVAILABLE:
        logger.error("Gemini not available - package not installed")
        return False

    key = api_key or os.getenv('GEMINI_API_KEY')
    if not key:
        logger.error("GEMINI_API_KEY not set in environment")
        return False

    genai.configure(api_key=key)
    logger.debug("Gemini API configured successfully")
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

YOUR WRITING STYLE:
- Voice: Professional technology analyst with expertise in AI governance
- Tone: Analytical and insightful, avoiding hype and marketing speak
- Focus on WHY developments matter, not just WHAT happened
- Include Canadian context and relevance when applicable
- Highlight implications for policy and business decisions

Article Title: {article.title}
Source: {article.source}
Category: {article.category or 'General'}
Original Content: {article.summary}

Your task is to write a concise, insightful summary for newsletter readers.

REQUIREMENTS:
1. Write EXACTLY 3-4 sentences - be concise and substantive
2. {style_instructions.get(style, style_instructions['detailed'])}
3. Include:
   - The core news/development
   - Key details, data points, or quotes if available
   - Context: Why is this significant in the broader AI landscape?
   - Implications: What does this mean for businesses, professionals, or policymakers?
   - Canadian relevance if applicable
4. Write in a professional, analytical tone - not hype or marketing speak
5. Use clear, readable prose (not bullet points)
6. Estimate reading time based on word count (assume 200 words per minute)

{"ALSO: Add a 'Commentary' section (2-3 sentences) with your analytical perspective on why this development matters and what readers should watch for." if include_commentary else ""}

Respond in JSON format:
{{
    "summary": "Your concise summary here (exactly 3-4 sentences)...",
    "commentary": "Your analytical commentary here (2-3 sentences)...",
    "read_time": "X min read"
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
        
    except json.JSONDecodeError as e:
        # If JSON parsing fails, use the raw response
        logger.warning(f"JSON parsing failed for article '{article.title[:50]}': {e}")
        article.ai_summary = response.text[:500] if response else article.summary
        article.ai_commentary = ""
    except Exception as e:
        logger.error(f"Summarization error for article '{article.title[:50]}': {e}")
        article.ai_summary = article.summary[:300]
        article.ai_commentary = ""

    return article


async def summarize_article_async(article: Article, config: dict) -> Article:
    """
    Async wrapper for article summarization.

    Args:
        article: Article to summarize
        config: Gemini configuration

    Returns:
        Article with AI summary
    """
    # Run the synchronous API call in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, summarize_article, article, config)


async def summarize_articles_async(articles: List[Article], config: dict,
                                   max_concurrent: int = 3) -> List[Article]:
    """
    Asynchronously generate AI summaries for a list of articles.
    Uses concurrent requests with rate limiting to avoid API throttling.

    Args:
        articles: List of articles to summarize
        config: Full configuration dictionary
        max_concurrent: Maximum concurrent API requests (default 3 to avoid rate limits)

    Returns:
        List of articles with AI summaries
    """
    gemini_config = config.get('gemini', {})
    semaphore = asyncio.Semaphore(max_concurrent)

    async def summarize_with_semaphore(article: Article) -> Article:
        """Summarize article with concurrency control."""
        async with semaphore:
            return await summarize_article_async(article, gemini_config)

    logger.info(f"Starting parallel summarization for {len(articles)} articles (max {max_concurrent} concurrent)")
    tasks = [summarize_with_semaphore(article) for article in articles]
    summarized = await asyncio.gather(*tasks)
    logger.info(f"Parallel summarization complete for {len(summarized)} articles")

    return summarized


def summarize_articles(articles: List[Article], config: dict,
                       progress_callback=None, parallel: bool = True) -> List[Article]:
    """
    Generate AI summaries for a list of articles.
    Can use parallel async calls for better performance.

    Args:
        articles: List of articles to summarize
        config: Full configuration dictionary
        progress_callback: Optional callback function for progress updates
        parallel: Use parallel async calls (default True)

    Returns:
        List of articles with AI summaries
    """
    gemini_config = config.get('gemini', {})

    if not init_gemini():
        logger.warning("Gemini not available - using original summaries")
        print("⚠️  Gemini not available - using original summaries")
        return articles

    print(f"\n🤖 Generating AI summaries for {len(articles)} articles...")
    logger.info(f"Starting summarization for {len(articles)} articles (parallel={parallel})")

    # Try parallel if requested, fall back to sequential
    if parallel and len(articles) > 1:
        try:
            # Check if there's already an event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    summarized = loop.run_until_complete(
                        summarize_articles_async(articles, config)
                    )
                finally:
                    loop.close()
            else:
                # Already have running loop, use sequential fallback
                logger.debug("Event loop already running, using sequential summarization")
                summarized = _summarize_articles_sequential(articles, gemini_config)
        except Exception as e:
            logger.warning(f"Parallel summarization failed, falling back to sequential: {e}")
            summarized = _summarize_articles_sequential(articles, gemini_config)
    else:
        summarized = _summarize_articles_sequential(articles, gemini_config)

    print("  ✓ Summarization complete")
    logger.info(f"Summarization complete for {len(summarized)} articles")

    return summarized


def _summarize_articles_sequential(articles: List[Article], config: dict) -> List[Article]:
    """Sequential fallback for article summarization."""
    summarized = []
    for i, article in enumerate(articles, 1):
        print(f"  [{i}/{len(articles)}] {article.title[:50]}...")
        summarized_article = summarize_article(article, config)
        summarized.append(summarized_article)
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
        model_name = config.get('gemini', {}).get('model', 'models/gemini-2.0-flash')
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
                
        return json.loads(response_text)
        
    except Exception as e:
        logger.error(f"Deep dive suggestion error: {e}")
        return {"topic": "AI Governance Trends", "reasoning": "Default suggestion"}


def generate_theme_of_week(articles: List[Article], config: dict) -> dict:
    """
    Generate a "Theme of the Week" - an editorial synthesis of the common
    thread across selected articles.
    
    Returns:
        Dictionary with theme title and editorial content
    """
    if not GEMINI_AVAILABLE or not init_gemini():
        return {"title": "", "content": "", "enabled": False}
    
    theme_config = config.get('theme_of_week', {})
    if not theme_config.get('enabled', True):
        return {"title": "", "content": "", "enabled": False}
    
    length = theme_config.get('length', 150)
    
    # Build article summaries for analysis
    articles_text = "\n".join([
        f"- [{a.category}] {a.title}: {a.summary[:200]}..." 
        for a in articles[:8]
    ])
    
    prompt = f"""You are the editor of "AI This Week", a professional newsletter for Canadian AI professionals and policymakers.

This week's selected articles:
{articles_text}

Write a "THEME OF THE WEEK" - an editorial insight (approximately {length} words) that:
1. Identifies the common thread or overarching narrative across these articles
2. Provides YOUR analytical perspective on what this week's news means for the AI landscape
3. Offers a forward-looking insight or question for readers to consider
4. Speaks directly to Canadian professionals and decision-makers

Write in first person ("This week, I noticed..." or "What strikes me about...").
Be insightful and thought-provoking, not just a summary.

Respond in JSON:
{{
    "title": "A compelling 5-8 word title for this week's theme",
    "content": "Your {length}-word editorial insight..."
}}
"""

    try:
        model_name = config.get('gemini', {}).get('model', 'models/gemini-2.0-flash')
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        result = json.loads(response_text)
        result['enabled'] = True
        return result
        
    except Exception as e:
        logger.error(f"Theme of week generation error: {e}")
        return {"title": "", "content": "", "enabled": False}
