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


def build_scott_voice_prompt(article: Article, section: str, config: dict, canadian_context: str = "") -> str:
    """
    Build a section-specific prompt in Scott's voice.

    Args:
        article: Article to summarize
        section: Newsletter section (headline, bright_spot, tool, deep_dive, grain_quality)
        config: Configuration dict
        canadian_context: Pre-generated Canadian angle (optional)

    Returns:
        Formatted prompt string
    """

    base_instructions = """You are writing for Scott's "AI This Week" newsletter - a premium professional resource for Canadian AI professionals, executives, and policymakers.

VOICE & TONE (Non-Negotiable):
- Professional but accessible: Not academic, not casual.
- Analytical: Always answer "So what?". Explain WHY things matter, not just WHAT happened.
- Policy-aware: Focus on governance, regulation, and societal impact.
- Balanced: Acknowledge both opportunities AND concerns (40% concerns, 35% opportunities, 25% neutral analysis).
- Business-focused: Emphasize economic and workforce transitions.
- Nuanced: Use hedging ("could", "may", "highlights", "risks"). Avoid sensationalism.
- Specific: Use data, numbers, and concrete studies where available.
- Connected: Show relationships between stories and broader trends.

WRITING RULES:
1. 2-3 sentences per paragraph maximum.
2. Use bullet points for lists to improve scannability.
3. Every summary MUST connect to the Canadian context.

CANADIAN FOCUS:""" + (f"\n{canadian_context}" if canadian_context else "")

    # Section-specific formatting
    section_formats = {
        'headline': """
Write 2-3 PARAGRAPHS covering:

PARAGRAPH 1 (Who/What):
- Who conducted the research/made the announcement? 
- What did they find/announce? Include specific numbers, percentages, data.
- 2-3 sentences.

PARAGRAPH 2 (Context & Implications):
- "So what?" - What does this mean? Why is it significant?
- How does this fit into the broader AI landscape?
- Use a balanced perspective (opportunities vs concerns).
- 2-3 sentences.

PARAGRAPH 3 (Canadian Angle - REQUIRED):
- How does this affect Canada specifically?
- Implications for Canadian professionals, policy, or business.
- 1-2 sentences.

CRITICAL: The summary MUST be 2-3 paragraphs with clear paragraph breaks (\\n\\n). Each paragraph should start with a specific focus as defined above.""",

        'bright_spot': """
Write 2 PARAGRAPHS highlighting a positive breakthrough or innovation:

PARAGRAPH 1: What happened and why it's impactful. Avoid hype; be analytical. (2-3 sentences)
PARAGRAPH 2: The broader benefit for society or innovation, with a focus on Canadian relevance if possible. (1-2 sentences)

Tone: Optimistic but grounded and nuanced.""",

        'deep_dive': """
Write 3-4 PARAGRAPHS for a longer research or policy analysis:

PARAGRAPH 1: Research question, methodology, or the core policy proposal. (2-3 sentences)
PARAGRAPH 2: Key findings with specific data points and numbers. (2-3 sentences)
PARAGRAPH 3: Broader implications for governance, ethics, or society. (2-3 sentences)
PARAGRAPH 4: Detailed Canadian relevance and "what to watch" in the coming months. (2-3 sentences)

Each paragraph on its own line for clarity.""",

        'tool': """
Write 2 PARAGRAPHS focused on practical utility:

PARAGRAPH 1: What the tool does, who it's for, and the specific problem it solves. (2-3 sentences)
PARAGRAPH 2: Potential use cases for Canadian professionals and practical utility. (1-2 sentences)

Focus on real utility, not marketing announcements.""",

        'grain_quality': """
Write 2 PARAGRAPHS on application in agriculture/grain:

PARAGRAPH 1: The specific AI application to grain quality or farming. (2-3 sentences)
PARAGRAPH 2: Impact on Canadian agriculture and practical benefits for producers. (1-2 sentences)"""
    }

    section_prompt = section_formats.get(section, section_formats['headline'])

    prompt = f"""{base_instructions}

Article Title: {article.title}
Source: {article.source}
Category: {article.category or 'General'}
Content: {article.summary}

{section_prompt}

Respond in JSON format (parse the JSON, handle markdown code blocks):
{{
    "summary": "Your multi-paragraph summary here. Use actual line breaks (\\n\\n) between paragraphs...",
    "canadian_context": "Specific Canadian angle or implication (1-2 sentences, optional)",
    "sentiment": "positive|negative|neutral|mixed"
}}"""

    return prompt


def generate_canadian_context(article: Article, config: dict) -> str:
    """
    Generate Canadian angle for articles that don't naturally have one.

    Returns: Canadian context string or empty string if not applicable
    """
    if not GEMINI_AVAILABLE:
        return ""

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return ""

    # Check if article already mentions Canada
    text = (article.title + " " + article.summary).lower()
    if any(keyword in text for keyword in ['canada', 'canadian', 'toronto', 'ottawa', 'montreal']):
        return ""  # Already has Canadian content

    try:
        genai.configure(api_key=api_key)
        model_name = config.get('gemini', {}).get('model', 'gemini-1.5-flash')

        prompt = f"""Generate a brief 1-2 sentence Canadian angle for this AI article.

Title: {article.title}
Summary: {article.summary[:300]}

Generate a sentence explaining how this relates to or impacts Canada, Canadian professionals, or Canadian policy.
Do NOT start with "For Canada," just provide the insight naturally.

Respond with ONLY the Canadian angle text (no JSON, no markdown, just plain text)."""

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        canadian_angle = response.text.strip()
        if canadian_angle and len(canadian_angle) > 10:
            logger.debug(f"Generated Canadian context for '{article.title[:40]}'")
            return canadian_angle

    except Exception as e:
        logger.debug(f"Could not generate Canadian context: {e}")

    return ""


def summarize_article(article: Article, config: dict, section: str = "headline") -> Article:
    """
    Generate AI summary and commentary for a single article using Scott's voice.

    Args:
        article: Article to summarize
        config: Gemini configuration
        section: Newsletter section for section-specific prompts

    Returns:
        Article with ai_summary, sentiment, and canadian_context populated
    """
    if not GEMINI_AVAILABLE:
        article.ai_summary = article.summary[:200] + "..."
        article.ai_commentary = ""
        article.sentiment = "neutral"
        return article

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.warning("GEMINI_API_KEY not set")
        article.ai_summary = article.summary[:200] + "..."
        article.sentiment = "neutral"
        return article

    model_name = config.get('model', 'gemini-1.5-flash')

    # Generate Canadian context if needed
    canadian_context = generate_canadian_context(article, config)

    # Build Scott's voice prompt
    prompt = build_scott_voice_prompt(article, section, config, canadian_context)

    try:
        genai.configure(api_key=api_key)
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
        article.sentiment = result.get('sentiment', 'neutral')
        article.canadian_context = canadian_context

        logger.debug(f"Summarized '{article.title[:50]}' for section '{section}' (sentiment: {article.sentiment})")

    except json.JSONDecodeError as e:
        # If JSON parsing fails, use the raw response
        logger.warning(f"JSON parsing failed for article '{article.title[:50]}': {e}")
        article.ai_summary = response.text[:500] if response else article.summary
        article.ai_commentary = ""
        article.sentiment = "neutral"
    except Exception as e:
        logger.error(f"Summarization error for article '{article.title[:50]}': {e}")
        article.ai_summary = article.summary[:300]
        article.ai_commentary = ""
        article.sentiment = "neutral"

    return article


async def summarize_article_async(article: Article, config: dict, section: str = "headline") -> Article:
    """
    Async wrapper for article summarization.

    Args:
        article: Article to summarize
        config: Gemini configuration
        section: Newsletter section for section-specific prompts

    Returns:
        Article with AI summary
    """
    # Run the synchronous API call in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, summarize_article, article, config, section)


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


# ============================================================================
# VIBECODING FRAMEWORK: The Editor Agent (YODA Filter)
# ============================================================================

def generate_curated_report(raw_intel_path: Path = None, output_path: Path = None, config: dict = None) -> dict:
    """
    The Editor Agent: Apply the Socratic YODA filter to raw intelligence.
    
    This function implements the three-level Socratic processing:
    - Level 1 (Exploration): Load all raw items
    - Level 2 (Examination): Filter by category relevance and quality
    - Level 3 (Expansion): Generate AI summaries with Scott's voice
    
    Args:
        raw_intel_path: Path to raw_intel.json
        output_path: Path to save curated_report.json
        config: Configuration dictionary
        
    Returns:
        The curated report dictionary
    """
    from pathlib import Path as PathLib
    
    if raw_intel_path is None:
        raw_intel_path = PathLib(__file__).parent.parent.parent / 'data' / 'raw_intel.json'
    
    if output_path is None:
        output_path = PathLib(__file__).parent.parent.parent / 'data' / 'curated_report.json'
    
    if config is None:
        config = {'gemini': {'model': 'models/gemini-2.0-flash'}}
    
    # Initialize Gemini
    if not init_gemini():
        logger.error("Cannot run Editor without Gemini API")
        return {}
    
    logger.info("=" * 60)
    logger.info("🧠 EDITOR AGENT: Applying YODA Filter")
    logger.info("=" * 60)
    
    # ========== LEVEL 1: EXPLORATION ==========
    logger.info("📖 Level 1 (Exploration): Loading raw intelligence...")
    
    try:
        with open(raw_intel_path, 'r', encoding='utf-8') as f:
            raw_intel = json.load(f)
    except FileNotFoundError:
        logger.error(f"Raw intel not found: {raw_intel_path}")
        return {}
    
    articles = raw_intel.get('articles', [])
    logger.info(f"   Loaded {len(articles)} raw items")
    
    # ========== LEVEL 2: EXAMINATION (The Filter) ==========
    logger.info("🔍 Level 2 (Examination): Filtering by relevance...")
    
    # Group by category
    categorized = {
        'headlines': [],
        'bright_spots': [],
        'tools': [],
        'deep_dives': [],
        'grain_quality': [],
        'learning': []
    }
    
    # Blacklist keywords for filtering out noise
    blacklist = ['crypto', 'nft', 'blockchain', 'bitcoin', 'metaverse', 'web3']
    
    for item in articles:
        title_lower = item.get('title', '').lower()
        summary_lower = item.get('summary', '').lower()
        content = f"{title_lower} {summary_lower}"
        
        # Skip blacklisted content
        if any(bl in content for bl in blacklist):
            continue
        
        category = item.get('category', 'headline')
        
        # Map source categories to newsletter sections
        if category == 'vertical_grain':
            categorized['grain_quality'].append(item)
        elif category == 'deep_dive':
            categorized['deep_dives'].append(item)
        elif category == 'tools':
            categorized['tools'].append(item)
        elif category == 'bright_spot':
            categorized['bright_spots'].append(item)
        else:
            categorized['headlines'].append(item)
    
    # Log filtering results
    for section, items in categorized.items():
        logger.info(f"   {section}: {len(items)} items")
    
    # ========== LEVEL 3: EXPANSION (Synthesis) ==========
    logger.info("✨ Level 3 (Expansion): Generating AI summaries...")
    
    curated = {
        'headlines': [],
        'bright_spots': [],
        'tools': [],
        'deep_dives': [],
        'grain_quality': [],
        'learning': [],
        'theme_of_week': None
    }
    
    # Process each section with AI summaries
    section_limits = {
        'headlines': 8,
        'bright_spots': 2,
        'tools': 2,
        'deep_dives': 4,
        'grain_quality': 5,
        'learning': 3
    }
    
    for section, items in categorized.items():
        limit = section_limits.get(section, 3)
        selected = items[:limit]
        
        if not selected:
            continue
            
        logger.info(f"   Processing {len(selected)} {section}...")
        
        for item in selected:
            # Create a minimal Article-like object for the prompt builder
            article = type('Article', (), {
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'summary': item.get('summary', ''),
                'source': item.get('source', ''),
                'category': section
            })()
            
            # Map section names for prompt
            prompt_section = section.rstrip('s')
            if prompt_section == 'headline':
                prompt_section = 'headline'
            elif prompt_section == 'grain_qualit':
                prompt_section = 'grain_quality'
            
            # Generate AI summary
            try:
                prompt = build_scott_voice_prompt(article, prompt_section, config)
                model_name = config.get('gemini', {}).get('model', 'models/gemini-2.0-flash')
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
                ai_summary = response.text.strip() if response.text else item.get('summary', '')
            except Exception as e:
                logger.warning(f"AI summary failed for '{item.get('title', '')[:30]}...': {e}")
                ai_summary = item.get('summary', '')
            
            curated[section].append({
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'summary': ai_summary,
                'source': item.get('source', ''),
            })
    
    # Generate Theme of the Week
    logger.info("   Generating Theme of the Week...")
    all_articles = []
    for section_items in curated.values():
        if isinstance(section_items, list):
            for item in section_items:
                # Create Article-like objects
                art = type('Article', (), {
                    'title': item.get('title', ''),
                    'category': 'general',
                    'summary': item.get('summary', '')[:200]
                })()
                all_articles.append(art)
    
    if all_articles:
        curated['theme_of_week'] = generate_theme_of_week(all_articles, config)
    
    # Save curated report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(curated, f, indent=2, ensure_ascii=False)
    
    logger.info("=" * 60)
    logger.info(f"💾 Curated report saved to: {output_path}")
    logger.info("=" * 60)
    
    return curated
