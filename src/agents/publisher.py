"""
Publisher Agent - The PDF Rendering Engine for the AI This Week Newsletter.

This agent converts structured JSON data (curated_report.json) into a
professionally formatted PDF document matching the "AI This Week" visual style.

Usage:
    python -m src.agents.publisher
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fpdf import FPDF

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def sanitize_text(text: str) -> str:
    """
    Sanitize text for PDF rendering by replacing problematic characters.
    fpdf2's built-in Helvetica font only supports latin-1 characters.
    """
    if not text:
        return ""
    
    # Replace common problematic characters
    replacements = {
        '\u2019': "'",    # Right single quotation mark
        '\u2018': "'",    # Left single quotation mark
        '\u201c': '"',    # Left double quotation mark
        '\u201d': '"',    # Right double quotation mark
        '\u2014': '-',    # Em dash
        '\u2013': '-',    # En dash
        '\u2026': '...',  # Ellipsis
        '\u00a0': ' ',    # Non-breaking space
        '\u2022': '*',    # Bullet
        '\u2611': '[x]',  # Ballot box with check
        '\u2610': '[ ]',  # Empty ballot box
        '\u00b0': ' degrees',  # Degree symbol
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Encode to latin-1 and back, replacing any remaining problematic chars
    try:
        text = text.encode('latin-1', errors='replace').decode('latin-1')
    except Exception:
        pass
    
    return text


class AIThisWeekPDF(FPDF):
    """
    Custom PDF class for the AI This Week newsletter.
    Handles the specific layout, fonts, and styling requirements.
    """

    def __init__(self):
        super().__init__()
        # Set margins: left, top, right
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=25)
        self.unicode_font = None  # Default to built-in fonts

    def header(self):
        """Draw the page header."""
        # Skip header on first page (we'll draw custom header there)
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, 'AI This Week | Key AI Developments You Should Know', 0, 1, 'C')
            self.ln(5)

    def footer(self):
        """Draw the page footer with disclaimer."""
        self.set_y(-25)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, 'Generative AI was used in the editing and creation of this message.', 0, 1, 'C')
        self.cell(0, 5, f'Page {self.page_no()}', 0, 0, 'C')

    def draw_email_header(self, sender: str = "Scott Hazlitt (CGC/CCG)"):
        """Draw the email-style header at the top of the first page."""
        # Email metadata
        self.set_font('Helvetica', '', 10)
        self.set_text_color(80, 80, 80)

        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

        self.cell(0, 6, f"From: {sender}", 0, 1)
        self.cell(0, 6, f"Sent: {timestamp}", 0, 1)
        self.cell(0, 6, "To: [Distribution List]", 0, 1)
        self.cell(0, 6, f"Subject: AI This Week | Key AI Developments You Should Know - {datetime.now().strftime('%B %d, %Y')}", 0, 1)

        self.ln(10)

        # Main title
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(26, 26, 46)  # Dark blue matching HTML
        self.cell(0, 12, 'AI This Week', 0, 1, 'C')

        self.set_font('Helvetica', '', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'Key AI Developments You Should Know', 0, 1, 'C')

        self.ln(10)

    def draw_section_header(self, title: str, emoji: str = ""):
        """Draw a section header with optional emoji."""
        self.ln(5)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(26, 26, 46)

        # Handle emoji - replace with bullet if font doesn't support
        display_title = f"{emoji} {title}" if emoji else title

        # Draw background box
        self.set_fill_color(240, 240, 245)
        self.cell(0, 10, display_title, 0, 1, 'L', fill=True)
        self.ln(3)

    def draw_article(self, article: Dict[str, Any], show_checkmark: bool = False):
        """Draw a single article entry."""
        # Calculate available width
        available_width = self.w - self.l_margin - self.r_margin

        # Title with optional checkmark
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(40, 40, 40)

        prefix = "[x] " if show_checkmark else ""  # Use [x] as checkmark substitute
        title = sanitize_text(article.get('title', 'Untitled'))

        self.multi_cell(available_width, 6, f"{prefix}{title}")

        # Summary
        summary = sanitize_text(article.get('summary', ''))
        if summary:
            self.set_font('Helvetica', '', 10)
            self.set_text_color(60, 60, 60)

            # Draw summary
            self.multi_cell(available_width, 5, summary)

        # Read more link
        link = article.get('link', '')
        if link:
            self.set_font('Helvetica', 'U', 9)
            self.set_text_color(0, 102, 204)
            self.cell(0, 6, 'Read more', 0, 1, link=link)

        self.ln(5)

    def draw_theme_of_week(self, theme: Dict[str, Any]):
        """Draw the Theme of the Week section with special styling."""
        if not theme or not theme.get('title'):
            return

        self.ln(5)

        # Store current position
        x = self.get_x()
        y = self.get_y()
        page_width = self.w - self.l_margin - self.r_margin

        # Calculate content heights (estimate)
        title_text = sanitize_text(theme.get('title', ''))
        content_text = sanitize_text(theme.get('content', ''))

        # Draw purple background box first
        box_height = 60  # Estimated height
        self.set_fill_color(102, 126, 234)  # #667eea
        self.rect(x, y, page_width, box_height, 'F')

        # Draw header
        self.set_xy(x + 5, y + 5)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, 'THEME OF THE WEEK', 0, 1)

        # Draw title
        self.set_x(x + 5)
        self.set_font('Helvetica', 'B', 14)
        self.multi_cell(page_width - 10, 7, title_text)

        # Draw content
        self.set_x(x + 5)
        self.set_font('Helvetica', 'I', 11)
        self.multi_cell(page_width - 10, 5, content_text)

        # Move past the box
        self.set_y(y + box_height + 5)
        self.set_text_color(0, 0, 0)  # Reset color


def load_curated_report(input_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the curated report JSON."""
    if input_path is None:
        input_path = Path(__file__).parent.parent.parent / 'data' / 'curated_report.json'

    if not input_path.exists():
        logger.warning(f"Curated report not found at {input_path}")
        return {}

    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_pdf(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Generate the AI This Week PDF from a curated report.

    Args:
        report: The curated report dictionary.
        output_path: Path for the output PDF.

    Returns:
        Path to the generated PDF.
    """
    if output_path is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
        output_path = Path(__file__).parent.parent.parent / 'output' / f'AI_This_Week_{date_str}.pdf'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = AIThisWeekPDF()
    pdf.add_page()

    # Draw email header
    pdf.draw_email_header()

    # ========== HEADLINES ==========
    headlines = report.get('headlines', report.get('headline', []))
    if headlines:
        pdf.draw_section_header("HEADLINE SUMMARY", "")

        for article in headlines[:8]:  # Max 8 headlines
            pdf.draw_article(article)

    # ========== BRIGHT SPOTS ==========
    bright_spots = report.get('bright_spots', report.get('bright_spot', []))
    if bright_spots:
        pdf.draw_section_header("BRIGHT SPOT OF THE WEEK", "")

        for article in bright_spots[:2]:
            pdf.draw_article(article)

    # ========== TOOLS ==========
    tools = report.get('tools', report.get('tool', []))
    if tools:
        pdf.draw_section_header("AI TOOL OF THE WEEK", "")

        for article in tools[:2]:
            pdf.draw_article(article)

    # ========== THEME OF THE WEEK ==========
    theme = report.get('theme_of_week', {})
    if theme:
        pdf.draw_theme_of_week(theme)

    # ========== DEEP DIVES ==========
    deep_dives = report.get('deep_dives', report.get('deep_dive', []))
    if deep_dives:
        pdf.draw_section_header("DEEP DIVE", "")

        for article in deep_dives[:4]:
            pdf.draw_article(article, show_checkmark=True)

    # ========== GRAIN QUALITY (Force new page) ==========
    grain_quality = report.get('grain_quality', [])
    if grain_quality:
        pdf.add_page()  # Force new page for Grain Quality
        pdf.draw_section_header("AI AND MACHINE LEARNING IN GRAIN QUALITY", "")

        for article in grain_quality:
            pdf.draw_article(article, show_checkmark=True)

        # Add internal reference footer
        pdf.ln(10)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, 'For more information - AI and Machine Learning in Grain Quality.docx', 0, 1)

    # ========== LEARNING ==========
    learning = report.get('learning', [])
    if learning:
        pdf.draw_section_header("LEARNING", "")

        for item in learning:
            if isinstance(item, dict):
                pdf.draw_article(item)
            else:
                pdf.set_font('Helvetica', '', 10)
                pdf.multi_cell(0, 5, str(item))

    # Save PDF
    pdf.output(str(output_path))
    logger.info(f"📄 PDF generated: {output_path}")

    return output_path


def main():
    """Main entry point for the Publisher agent."""
    logger.info("=" * 60)
    logger.info("📄 PUBLISHER AGENT: Generating PDF")
    logger.info("=" * 60)

    report = load_curated_report()

    if not report:
        logger.error("No curated report found. Run the Editor first.")
        return

    output_path = generate_pdf(report)
    logger.info(f"✅ PDF saved to: {output_path}")


if __name__ == '__main__':
    main()
