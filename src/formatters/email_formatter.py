#!/usr/bin/env python3
"""
Email Formatting Module

Generates Outlook-compatible HTML emails matching the "AI This Week" style.
Uses a table-based layout for proper rendering in Outlook.
"""

from typing import List
from datetime import datetime
from pathlib import Path

# Import from parent
import sys
sys.path.append(str(Path(__file__).parent.parent))
from sources.rss_fetcher import Article


def get_category_emoji(category: str) -> str:
    """Get emoji for article category."""
    emojis = {
        'governance': '⚖️',
        'capabilities': '🚀',
        'business': '💼',
        'education': '📚',
        'tools': '🛠️',
        'research': '🔬',
        'uncategorized': '📰'
    }
    return emojis.get(category.lower(), '📰')


def format_date(dt: datetime) -> str:
    """Format date for display."""
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y")


def format_newsletter_html(articles: List[Article], config: dict, 
                           tool_of_week: dict = None,
                           learning_items: List[dict] = None,
                           deep_dive: dict = None,
                           theme_of_week: dict = None) -> str:
    """
    Generate complete newsletter HTML matching AI This Week style.
    
    Uses table-based layout with category headers, similar to the user's
    original newsletter format.
    """
    newsletter_config = config.get('newsletter', {})
    newsletter_name = newsletter_config.get('name', 'AI This Week')
    tagline = newsletter_config.get('tagline', 'Key AI Developments You Should Know')
    
    today = datetime.now()
    week_of = format_date(today)
    
    # Group articles by category
    categories = {}
    for article in articles:
        cat = article.category or "uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)
    
    # Build articles HTML - organized by category
    articles_html = ""
    
    for cat in ['governance', 'capabilities', 'business', 'education', 'tools', 'research', 'uncategorized']:
        if cat not in categories:
            continue
            
        cat_articles = categories[cat]
        emoji = get_category_emoji(cat)
        
        # Category header
        articles_html += f'''
        <tr>
            <td style="padding: 20px 30px 10px 30px; background-color: #f8f9fa; border-top: 3px solid #1a1a2e;">
                <h3 style="color: #1a1a2e; margin: 0; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">
                    {emoji} {cat.title()}
                </h3>
            </td>
        </tr>
        '''
        
        # Articles in this category
        for article in cat_articles:
            summary = article.ai_summary if article.ai_summary else article.summary
            commentary = article.ai_commentary if hasattr(article, 'ai_commentary') else ""
            
            # Don't truncate - show full AI-generated summary
            
            articles_html += f'''
        <tr>
            <td style="padding: 15px 30px; border-bottom: 1px solid #eee;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td valign="top" width="100%">
                            <a href="{article.url}" style="color: #1a1a2e; text-decoration: none; font-size: 16px; font-weight: 600; line-height: 1.4; display: block; margin-bottom: 8px;">{article.title}</a>
                            <p style="color: #444444; margin: 0 0 8px 0; font-size: 14px; line-height: 1.6;">{summary}</p>
                            {f'<p style="color: #666666; margin: 0 0 8px 0; font-size: 13px; line-height: 1.5; font-style: italic; border-left: 2px solid #667eea; padding-left: 10px;">💡 {commentary}</p>' if commentary else ''}
                            <p style="margin: 0;">
                                <span style="color: #888888; font-size: 12px;">{article.source}</span>
                                <span style="color: #cccccc;"> | </span>
                                <a href="{article.url}" style="color: #667eea; text-decoration: none; font-size: 12px; font-weight: 500;">Read more →</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
            '''
    
    # Tool of the Week section
    tool_html = ""
    if tool_of_week:
        tool_html = f'''
        <tr>
            <td style="padding: 25px 30px; background-color: #1a1a2e;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td>
                            <h2 style="color: #ffffff; margin: 0 0 15px 0; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">🛠️ Tool of the Week</h2>
                            <h3 style="color: #667eea; margin: 0 0 10px 0; font-size: 18px;">{tool_of_week.get('name', '')}</h3>
                            <p style="color: #cccccc; margin: 0 0 15px 0; font-size: 14px; line-height: 1.5;">{tool_of_week.get('description', '')}</p>
                            <a href="{tool_of_week.get('url', '#')}" style="display: inline-block; background-color: #667eea; color: white; padding: 8px 20px; border-radius: 4px; text-decoration: none; font-size: 13px; font-weight: 500;">Try it →</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        '''
    
    # Learning section
    learning_html = ""
    if learning_items:
        items = "".join([
            f'<tr><td style="padding: 8px 0;"><span style="color: #667eea; font-weight: bold;">▸</span> {item.get("title", "")} — <a href="{item.get("url", "#")}" style="color: #667eea; text-decoration: none;">{item.get("type", "Link")}</a></td></tr>' 
            for item in learning_items
        ])
        learning_html = f'''
        <tr>
            <td style="padding: 25px 30px; background-color: #f8f9fa;">
                <h2 style="color: #1a1a2e; margin: 0 0 15px 0; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">📚 Learning</h2>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="font-size: 14px; color: #444;">
                    {items}
                </table>
            </td>
        </tr>
        '''
    
    # Theme of the Week section
    theme_html = ""
    if theme_of_week and theme_of_week.get('enabled') and theme_of_week.get('content'):
        theme_html = f'''
        <tr>
            <td style="padding: 0;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px 30px;">
                            <h2 style="color: #ffffff; margin: 0 0 5px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; opacity: 0.8;">💡 Theme of the Week</h2>
                            <h3 style="color: #ffffff; margin: 0 0 15px 0; font-size: 20px; font-weight: 600; line-height: 1.3;">{theme_of_week.get('title', '')}</h3>
                            <p style="color: #e8e8ff; margin: 0; font-size: 15px; line-height: 1.7; font-style: italic;">{theme_of_week.get('content', '')}</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        '''
    
    # Complete HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{newsletter_name} - {week_of}</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}
        .article-title {{font-size: 16px !important;}}
    </style>
    <![endif]-->
    <style>
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f4; -webkit-font-smoothing: antialiased;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center" style="padding: 20px 10px;">
                <table role="presentation" class="container" width="650" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #1a1a2e; padding: 35px 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                🤖 {newsletter_name}
                            </h1>
                            <p style="color: #a0a0a0; margin: 10px 0 0 0; font-size: 14px; font-weight: 400;">{tagline}</p>
                        </td>
                    </tr>
                    
                    <!-- Intro -->
                    <tr>
                        <td style="padding: 25px 30px; border-bottom: 1px solid #eee;">
                            <p style="color: #444444; margin: 0; font-size: 15px; line-height: 1.6;">
                                <strong>Hello,</strong>
                            </p>
                            <p style="color: #444444; margin: 10px 0 0 0; font-size: 15px; line-height: 1.6;">
                                Here are this week's key AI developments you should know about.
                            </p>
                            <p style="color: #888888; margin: 10px 0 0 0; font-size: 13px;">
                                📅 Week of {week_of}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Section Header -->
                    <tr>
                        <td style="padding: 20px 30px 10px 30px;">
                            <h2 style="color: #1a1a2e; margin: 0; font-size: 18px; font-weight: 700;">
                                📰 Key Developments
                            </h2>
                        </td>
                    </tr>
                    
                    <!-- Articles by Category -->
                    {articles_html}
                    
                    <!-- Tool of the Week -->
                    {tool_html}
                    
                    <!-- Theme of the Week -->
                    {theme_html}
                    
                    <!-- Learning -->
                    {learning_html}
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #1a1a2e; padding: 25px 30px; text-align: center;">
                            <p style="color: #888888; margin: 0 0 5px 0; font-size: 12px;">
                                Curated with 🤖 by AI Newsletter Bot
                            </p>
                            <p style="color: #666666; margin: 0; font-size: 11px;">
                                {today.strftime("%B %d, %Y")}
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
    
    return html


def format_paragraphs(text: str) -> str:
    """
    Convert multi-paragraph text (with \\n\\n separators) to HTML <p> tags.

    Args:
        text: Text with paragraphs separated by double newlines

    Returns:
        HTML with <p> tags for each paragraph
    """
    if not text:
        return ""

    # Split on double newlines
    paragraphs = text.split('\n\n')
    html_paragraphs = []

    for para in paragraphs:
        para = para.strip()
        if para:  # Only add non-empty paragraphs
            html_paragraphs.append(f'<p style="color: #444444; margin: 0 0 12px 0; font-size: 14px; line-height: 1.6;">{para}</p>')

    return ''.join(html_paragraphs)


def build_headline_section(articles: List[Article]) -> str:
    """Build Headline Summary section with 2-3 paragraph summaries."""
    if not articles:
        return ""

    headlines_html = f'''
    <tr>
        <td style="padding: 20px 30px 10px 30px;">
            <h2 style="color: #1a1a2e; margin: 0; font-size: 18px; font-weight: 700;">
                📰 HEADLINE SUMMARY
            </h2>
        </td>
    </tr>
    '''

    for article in articles:
        summary = article.ai_summary if article.ai_summary else article.summary

        headlines_html += f'''
    <tr>
        <td style="padding: 15px 30px; border-bottom: 1px solid #eee;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                    <td valign="top" width="100%">
                        <h3 style="color: #1a1a2e; margin: 0 0 10px 0; font-size: 15px; font-weight: 600; line-height: 1.4;">
                            🔹 <a href="{article.url}" style="color: #1a1a2e; text-decoration: none;">{article.title}</a>
                        </h3>
                        {format_paragraphs(summary)}
                        <p style="margin: 0; margin-top: 8px;">
                            <span style="color: #888888; font-size: 12px;">{article.source}</span>
                            <span style="color: #cccccc;"> | </span>
                            <a href="{article.url}" style="color: #667eea; text-decoration: none; font-size: 12px; font-weight: 500;">Read more →</a>
                        </p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    '''

    return headlines_html


def build_bright_spot_section(articles: List[Article]) -> str:
    """Build Bright Spot of the Week section."""
    if not articles:
        return ""

    bright_html = f'''
    <tr>
        <td style="padding: 20px 30px 10px 30px;">
            <h2 style="color: #1a1a2e; margin: 0; font-size: 18px; font-weight: 700;">
                ✨ BRIGHT SPOT OF THE WEEK
            </h2>
        </td>
    </tr>
    '''

    for article in articles:
        summary = article.ai_summary if article.ai_summary else article.summary

        bright_html += f'''
    <tr>
        <td style="padding: 15px 30px; border-bottom: 1px solid #eee;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                    <td valign="top" width="100%">
                        <h3 style="color: #1a1a2e; margin: 0 0 10px 0; font-size: 15px; font-weight: 600; line-height: 1.4;">
                            <a href="{article.url}" style="color: #1a1a2e; text-decoration: none;">{article.title}</a>
                        </h3>
                        {format_paragraphs(summary)}
                        <p style="margin: 0; margin-top: 8px;">
                            <a href="{article.url}" style="color: #667eea; text-decoration: none; font-size: 12px; font-weight: 500;">Read more →</a>
                        </p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    '''

    return bright_html


def build_tool_section(articles: List[Article]) -> str:
    """Build Tool of the Week section."""
    if not articles:
        return ""

    article = articles[0]  # Only show first tool
    summary = article.ai_summary if article.ai_summary else article.summary

    tool_html = f'''
    <tr>
        <td style="padding: 25px 30px; background-color: #1a1a2e;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                    <td>
                        <h2 style="color: #ffffff; margin: 0 0 15px 0; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">🛠️ TOOL OF THE WEEK</h2>
                        <h3 style="color: #667eea; margin: 0 0 10px 0; font-size: 16px;">
                            <a href="{article.url}" style="color: #667eea; text-decoration: none;">{article.title}</a>
                        </h3>
                        <div style="color: #cccccc; margin: 0 0 15px 0; font-size: 14px; line-height: 1.5;">
                            {format_paragraphs(summary).replace('color: #444444', 'color: #cccccc')}
                        </div>
                        <a href="{article.url}" style="display: inline-block; background-color: #667eea; color: white; padding: 8px 20px; border-radius: 4px; text-decoration: none; font-size: 13px; font-weight: 500;">Try it →</a>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    '''

    return tool_html


def build_learning_section() -> str:
    """Build Learning section (placeholder for manual curation)."""
    learning_html = f'''
    <tr>
        <td style="padding: 25px 30px; background-color: #f8f9fa;">
            <h2 style="color: #1a1a2e; margin: 0 0 15px 0; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">📚 LEARNING</h2>
            <p style="color: #666666; margin: 0; font-size: 13px; font-style: italic;">
                Events, courses, and webinars coming this week.
            </p>
        </td>
    </tr>
    '''
    return learning_html


def build_deep_dive_section(articles: List[Article]) -> str:
    """Build Deep Dive section with 3-4 paragraph analysis pieces."""
    if not articles:
        return ""

    deep_html = f'''
    <tr>
        <td style="padding: 20px 30px 10px 30px;">
            <h2 style="color: #1a1a2e; margin: 0; font-size: 18px; font-weight: 700;">
                📊 DEEP DIVE
            </h2>
        </td>
    </tr>
    '''

    for article in articles:
        summary = article.ai_summary if article.ai_summary else article.summary

        deep_html += f'''
    <tr>
        <td style="padding: 15px 30px; border-bottom: 1px solid #eee;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                    <td valign="top" width="100%">
                        <h3 style="color: #1a1a2e; margin: 0 0 10px 0; font-size: 15px; font-weight: 600; line-height: 1.4;">
                            <a href="{article.url}" style="color: #1a1a2e; text-decoration: none;">{article.title}</a>
                        </h3>
                        {format_paragraphs(summary)}
                        <p style="margin: 0; margin-top: 8px;">
                            <span style="color: #888888; font-size: 12px;">{article.source}</span>
                            <span style="color: #cccccc;"> | </span>
                            <a href="{article.url}" style="color: #667eea; text-decoration: none; font-size: 12px; font-weight: 500;">Read more →</a>
                        </p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    '''

    return deep_html


def build_grain_quality_section(articles: List[Article]) -> str:
    """Build optional Grain Quality section for agriculture/farming AI."""
    if not articles:
        return ""

    grain_html = f'''
    <tr>
        <td style="padding: 20px 30px 10px 30px;">
            <h2 style="color: #1a1a2e; margin: 0; font-size: 18px; font-weight: 700;">
                🌾 GRAIN QUALITY
            </h2>
        </td>
    </tr>
    '''

    for article in articles:
        summary = article.ai_summary if article.ai_summary else article.summary

        grain_html += f'''
    <tr>
        <td style="padding: 15px 30px; border-bottom: 1px solid #eee;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                    <td valign="top" width="100%">
                        <h3 style="color: #1a1a2e; margin: 0 0 10px 0; font-size: 15px; font-weight: 600; line-height: 1.4;">
                            <a href="{article.url}" style="color: #1a1a2e; text-decoration: none;">{article.title}</a>
                        </h3>
                        {format_paragraphs(summary)}
                        <p style="margin: 0; margin-top: 8px;">
                            <a href="{article.url}" style="color: #667eea; text-decoration: none; font-size: 12px; font-weight: 500;">Read more →</a>
                        </p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    '''

    return grain_html


def format_newsletter_html_sections(selected_articles: dict, config: dict) -> str:
    """
    Generate newsletter HTML using Scott's section-based format.

    Args:
        selected_articles: Dict with section keys (headlines, bright_spots, tools, deep_dives, grain_quality)
        config: Configuration dict

    Returns:
        Complete HTML newsletter
    """
    newsletter_config = config.get('newsletter', {})
    newsletter_name = newsletter_config.get('name', 'AI This Week')
    tagline = newsletter_config.get('tagline', 'Key AI Developments You Should Know')

    today = datetime.now()
    week_of = format_date(today)

    # Build sections
    headlines_html = build_headline_section(selected_articles.get('headlines', []))
    bright_spot_html = build_bright_spot_section(selected_articles.get('bright_spots', []))
    tool_html = build_tool_section(selected_articles.get('tools', []))
    learning_html = build_learning_section()
    deep_dive_html = build_deep_dive_section(selected_articles.get('deep_dives', []))
    grain_html = build_grain_quality_section(selected_articles.get('grain_quality', []))

    # Complete HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{newsletter_name} - {week_of}</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}
        .article-title {{font-size: 16px !important;}}
    </style>
    <![endif]-->
    <style>
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f4; -webkit-font-smoothing: antialiased;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center" style="padding: 20px 10px;">
                <table role="presentation" class="container" width="650" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="background-color: #1a1a2e; padding: 35px 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                🤖 {newsletter_name}
                            </h1>
                            <p style="color: #a0a0a0; margin: 10px 0 0 0; font-size: 14px; font-weight: 400;">{tagline}</p>
                        </td>
                    </tr>

                    <!-- Intro -->
                    <tr>
                        <td style="padding: 25px 30px; border-bottom: 1px solid #eee;">
                            <p style="color: #444444; margin: 0; font-size: 15px; line-height: 1.6;">
                                <strong>Hello,</strong>
                            </p>
                            <p style="color: #444444; margin: 10px 0 0 0; font-size: 15px; line-height: 1.6;">
                                Here's your weekly update on the latest in AI.
                            </p>
                            <p style="color: #888888; margin: 10px 0 0 0; font-size: 13px;">
                                📅 Week of {week_of}
                            </p>
                        </td>
                    </tr>

                    <!-- Headline Summary -->
                    {headlines_html}

                    <!-- Bright Spot -->
                    {bright_spot_html}

                    <!-- Tool of the Week -->
                    {tool_html}

                    <!-- Learning -->
                    {learning_html}

                    <!-- Deep Dive -->
                    {deep_dive_html}

                    <!-- Grain Quality (optional) -->
                    {grain_html}

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #1a1a2e; padding: 25px 30px; text-align: center;">
                            <p style="color: #888888; margin: 0 0 5px 0; font-size: 12px;">
                                Curated with 🤖 by Scott's AI Newsletter Bot
                            </p>
                            <p style="color: #666666; margin: 0; font-size: 11px;">
                                {today.strftime("%B %d, %Y")}
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

    return html


def save_newsletter(html: str, output_dir: Path, filename: str = None) -> Path:
    """Save newsletter HTML to file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = f"newsletter_{datetime.now().strftime('%Y-%m-%d')}.html"

    output_path = output_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_path
