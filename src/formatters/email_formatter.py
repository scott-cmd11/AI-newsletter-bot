#!/usr/bin/env python3
"""
Email Formatting Module

Generates Outlook-compatible HTML emails from processed articles.
"""

from typing import List
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Import from parent
import sys
sys.path.append(str(Path(__file__).parent.parent))
from sources.rss_fetcher import Article


def get_category_color(category: str) -> str:
    """Get accent color for article category."""
    colors = {
        'governance': '#8B5CF6',      # Purple
        'capabilities': '#3B82F6',    # Blue  
        'business': '#10B981',        # Green
        'education': '#F59E0B',       # Amber
        'tools': '#EC4899',           # Pink
        'research': '#6366F1',        # Indigo
    }
    return colors.get(category.lower(), '#6B7280')  # Gray default


def format_date(dt: datetime) -> str:
    """Format date for display."""
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y")


def format_newsletter_html(articles: List[Article], config: dict, 
                           tool_of_week: dict = None,
                           learning_items: List[dict] = None,
                           deep_dive: dict = None) -> str:
    """
    Generate complete newsletter HTML.
    
    Args:
        articles: List of scored and summarized articles
        config: Newsletter configuration
        tool_of_week: Optional tool of the week data
        learning_items: Optional list of learning resources
        deep_dive: Optional deep dive topic data
        
    Returns:
        Complete HTML string ready for Outlook
    """
    newsletter_config = config.get('newsletter', {})
    newsletter_name = newsletter_config.get('name', 'AI This Week')
    tagline = newsletter_config.get('tagline', 'Key AI Developments You Should Know')
    
    today = datetime.now()
    week_of = format_date(today)
    
    # Build articles HTML
    articles_html = ""
    for article in articles:
        category_color = get_category_color(article.category)
        summary = article.ai_summary if article.ai_summary else article.summary
        commentary = article.ai_commentary
        
        articles_html += f'''
        <tr>
            <td style="padding: 15px 30px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td style="border-left: 4px solid {category_color}; padding-left: 15px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <td>
                                        <span style="display: inline-block; background-color: {category_color}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">{article.category or 'News'}</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 5px;">
                                        <a href="{article.url}" style="color: #1a1a1a; text-decoration: none; font-size: 18px; font-weight: bold; line-height: 1.3;">{article.title}</a>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 10px;">
                                        <p style="color: #4a4a4a; margin: 0; font-size: 14px; line-height: 1.6;">{summary}</p>
                                        {f'<p style="color: #6a6a6a; margin: 10px 0 0 0; font-size: 13px; font-style: italic; line-height: 1.5;">💡 {commentary}</p>' if commentary else ''}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 10px;">
                                        <span style="color: #888888; font-size: 12px;">{article.source}</span>
                                        <span style="color: #cccccc; font-size: 12px;"> • </span>
                                        <span style="color: #888888; font-size: 12px;">{format_date(article.published)}</span>
                                        <span style="color: #cccccc; font-size: 12px;"> • </span>
                                        <a href="{article.url}" style="color: #667eea; text-decoration: none; font-size: 12px;">Read more →</a>
                                    </td>
                                </tr>
                            </table>
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
            <td style="padding: 20px 30px; background-color: #f8f9fa;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td>
                            <h2 style="color: #333333; margin: 0 0 15px 0; font-size: 18px;">🛠️ Tool of the Week</h2>
                            <h3 style="color: #667eea; margin: 0 0 10px 0; font-size: 16px;">{tool_of_week.get('name', '')}</h3>
                            <p style="color: #4a4a4a; margin: 0; font-size: 14px; line-height: 1.5;">{tool_of_week.get('description', '')}</p>
                            <a href="{tool_of_week.get('url', '#')}" style="display: inline-block; margin-top: 10px; color: #667eea; text-decoration: none; font-size: 13px;">Try it →</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        '''
    
    # Learning section
    learning_html = ""
    if learning_items:
        items = "".join([f'<li style="margin-bottom: 8px;">{item.get("title", "")} - <a href="{item.get("url", "#")}" style="color: #667eea;">{item.get("type", "Link")}</a></li>' for item in learning_items])
        learning_html = f'''
        <tr>
            <td style="padding: 20px 30px;">
                <h2 style="color: #333333; margin: 0 0 15px 0; font-size: 18px;">📚 Learning</h2>
                <ul style="color: #4a4a4a; margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6;">
                    {items}
                </ul>
            </td>
        </tr>
        '''
    
    # Deep Dive section
    deep_dive_html = ""
    if deep_dive:
        deep_dive_html = f'''
        <tr>
            <td style="padding: 20px 30px; background-color: #667eea;">
                <h2 style="color: #ffffff; margin: 0 0 10px 0; font-size: 18px;">🔍 Deep Dive</h2>
                <h3 style="color: #ffffff; margin: 0 0 10px 0; font-size: 16px;">{deep_dive.get('topic', '')}</h3>
                <p style="color: #e0e0ff; margin: 0; font-size: 14px; line-height: 1.5;">{deep_dive.get('reasoning', '')}</p>
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
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background-color: #f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center" style="padding: 20px 0;">
                <table role="presentation" width="650" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 35px 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: bold;">🤖 {newsletter_name}</h1>
                            <p style="color: #e0e0e0; margin: 10px 0 0 0; font-size: 14px;">{tagline}</p>
                        </td>
                    </tr>
                    
                    <!-- Date -->
                    <tr>
                        <td style="padding: 20px 30px 10px 30px; border-bottom: 1px solid #eeeeee;">
                            <p style="color: #666666; margin: 0; font-size: 14px;">📅 Week of {week_of}</p>
                        </td>
                    </tr>
                    
                    <!-- Key Developments Header -->
                    <tr>
                        <td style="padding: 20px 30px 10px 30px;">
                            <h2 style="color: #333333; margin: 0; font-size: 20px; font-weight: bold;">📰 Key Developments</h2>
                        </td>
                    </tr>
                    
                    <!-- Articles -->
                    {articles_html}
                    
                    <!-- Divider -->
                    <tr>
                        <td style="padding: 0 30px;">
                            <hr style="border: none; border-top: 1px solid #eeeeee; margin: 20px 0;">
                        </td>
                    </tr>
                    
                    <!-- Tool of the Week -->
                    {tool_html}
                    
                    <!-- Learning -->
                    {learning_html}
                    
                    <!-- Deep Dive -->
                    {deep_dive_html}
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f8f8; padding: 25px 30px; text-align: center; border-top: 1px solid #eeeeee;">
                            <p style="color: #999999; margin: 0 0 5px 0; font-size: 12px;">Generated by AI Newsletter Bot</p>
                            <p style="color: #bbbbbb; margin: 0; font-size: 11px;">{today.strftime("%Y-%m-%d %H:%M")}</p>
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
    """
    Save newsletter HTML to file.
    
    Returns:
        Path to saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not filename:
        filename = f"newsletter_{datetime.now().strftime('%Y-%m-%d')}.html"
        
    output_path = output_dir / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    return output_path
