"""
Vercel serverless entry point for Flask app.

This module serves as the entry point for the Flask application when deployed on Vercel.
It handles the serverless environment and ensures proper initialization.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
src_dir = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_dir)

# Create persistent directory in Vercel's /tmp (good for session data)
# Note: This persists during function lifetime but not between cold starts
output_dir = Path("/tmp/newsletter-output")
output_dir.mkdir(exist_ok=True, parents=True)

# Set OUTPUT_DIR environment variable for the Flask app
os.environ["OUTPUT_DIR"] = str(output_dir)

# Import the Flask app
from web import app

# Export app for Vercel (WSGI)
# Vercel will call this automatically
