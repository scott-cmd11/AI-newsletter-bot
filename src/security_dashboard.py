#!/usr/bin/env python3
"""
Security Dashboard - Monitor authentication, rate limiting, and API usage.

Linear/Vercel aesthetic design with real-time metrics display.
"""

import json
import logging
import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template_string, request, jsonify, Response

# Import rate limiter stats
from src.rate_limiter import _rate_limits, WINDOW_SECONDS, MAX_REQUESTS

logger = logging.getLogger(__name__)

# Security Dashboard Template
SECURITY_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #09090b;
            --bg-surface: #18181b;
            --bg-elevated: #27272a;
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-default: rgba(255, 255, 255, 0.1);
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent-glow: rgba(99, 102, 241, 0.15);
            --accent-border: rgba(99, 102, 241, 0.5);
            --success: #22c55e;
            --warning: #eab308;
            --error: #ef4444;
            --font-sans: 'Inter', -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            --letter-spacing-tight: -0.02em;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: var(--font-sans);
            background: var(--bg-primary);
            min-height: 100vh;
            color: var(--text-primary);
            font-size: 13px;
            -webkit-font-smoothing: antialiased;
        }
        
        .header {
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border-subtle);
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: var(--letter-spacing-tight);
        }
        
        .header-nav {
            display: flex;
            gap: 4px;
        }
        
        .nav-link {
            padding: 8px 12px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            border-radius: 4px;
            transition: all 0.15s ease;
        }
        
        .nav-link:hover {
            color: var(--text-primary);
            background: var(--accent-glow);
        }
        
        .nav-link.active {
            color: var(--text-primary);
            background: var(--accent-glow);
            box-shadow: inset 0 0 0 1px var(--accent-border);
        }
        
        .status-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 500;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: var(--success);
        }
        
        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .page-title {
            font-size: 20px;
            font-weight: 600;
            letter-spacing: var(--letter-spacing-tight);
            margin-bottom: 20px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 16px;
        }
        
        .panel {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .panel-header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-subtle);
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }
        
        .panel-content {
            padding: 16px;
        }
        
        /* Rate Limit Meters */
        .meter-group {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .meter {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        
        .meter-label {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
        }
        
        .meter-name {
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .meter-value {
            font-family: var(--font-mono);
            color: var(--text-muted);
            font-size: 11px;
        }
        
        .meter-bar {
            height: 4px;
            background: var(--bg-elevated);
            border-radius: 2px;
            overflow: hidden;
        }
        
        .meter-fill {
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }
        
        .meter-fill.low { background: var(--success); }
        .meter-fill.medium { background: var(--warning); }
        .meter-fill.high { background: var(--error); }
        
        /* Logs Table */
        .logs-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .logs-table th,
        .logs-table td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-subtle);
        }
        
        .logs-table th {
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            background: var(--bg-elevated);
        }
        
        .logs-table td {
            font-size: 12px;
        }
        
        .logs-table tr:hover td {
            background: var(--bg-elevated);
        }
        
        .mono {
            font-family: var(--font-mono);
            font-size: 11px;
        }
        
        .text-muted {
            color: var(--text-muted);
        }
        
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 500;
            font-family: var(--font-mono);
        }
        
        .badge-success {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: var(--success);
        }
        
        .badge-error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: var(--error);
        }
        
        .badge-warning {
            background: rgba(234, 179, 8, 0.1);
            border: 1px solid rgba(234, 179, 8, 0.3);
            color: var(--warning);
        }
        
        /* Stats */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .stat-card {
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            padding: 12px;
        }
        
        .stat-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 4px;
        }
        
        .stat-value {
            font-family: var(--font-mono);
            font-size: 20px;
            font-weight: 600;
            letter-spacing: var(--letter-spacing-tight);
        }
        
        .stat-value.success { color: var(--success); }
        .stat-value.warning { color: var(--warning); }
        .stat-value.error { color: var(--error); }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-muted);
        }
        
        .btn {
            padding: 6px 12px;
            border: 1px solid var(--border-default);
            border-radius: 6px;
            font-weight: 500;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.15s ease;
            background: transparent;
            color: var(--text-secondary);
            font-family: var(--font-sans);
        }
        
        .btn:hover {
            border-color: rgba(255,255,255,0.2);
            color: var(--text-primary);
            background: var(--accent-glow);
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-left">
            <span class="logo">
                <span>◆</span>
                Newsletter Curator
            </span>
            <nav class="header-nav">
                <a href="/" class="nav-link">Curate</a>
                <a href="/security" class="nav-link active">Security</a>
            </nav>
        </div>
        <div class="status-pill">
            <span class="status-dot"></span>
            Operational
        </div>
    </header>
    
    <div class="container">
        <h1 class="page-title">Security Overview</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Auth Status</div>
                <div class="stat-value success" id="auth-status">{{ 'Enabled' if auth_enabled else 'Disabled' }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Rate Limit</div>
                <div class="stat-value">{{ max_requests }}/min</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active IPs</div>
                <div class="stat-value" id="active-ips">{{ active_ips }}</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="panel">
                <div class="panel-header">Rate Limiting Status</div>
                <div class="panel-content">
                    <div class="meter-group" id="rate-meters">
                        {% if rate_stats %}
                            {% for ip, stats in rate_stats.items() %}
                            <div class="meter">
                                <div class="meter-label">
                                    <span class="meter-name mono">{{ ip }}</span>
                                    <span class="meter-value">{{ stats.count }}/{{ max_requests }}</span>
                                </div>
                                <div class="meter-bar">
                                    <div class="meter-fill {% if stats.percent < 50 %}low{% elif stats.percent < 80 %}medium{% else %}high{% endif %}" 
                                         style="width: {{ stats.percent }}%"></div>
                                </div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="empty-state">No active rate limits</div>
                        {% endif %}
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <span>Recent Activity</span>
                </div>
                <table class="logs-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Event</th>
                            <th>IP Address</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="activity-log">
                        {% for log in activity_logs %}
                        <tr>
                            <td class="mono text-muted">{{ log.time }}</td>
                            <td>{{ log.event }}</td>
                            <td class="mono">{{ log.ip }}</td>
                            <td>
                                <span class="badge {% if log.status == 'success' %}badge-success{% elif log.status == 'blocked' %}badge-error{% else %}badge-warning{% endif %}">
                                    {{ log.status }}
                                </span>
                            </td>
                        </tr>
                        {% endfor %}
                        {% if not activity_logs %}
                        <tr>
                            <td colspan="4" class="empty-state">No recent activity</td>
                        </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 5 seconds
        setInterval(() => {
            fetch('/security/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('active-ips').textContent = data.active_ips;
                    // Could update meters here too
                });
        }, 5000);
    </script>
</body>
</html>
'''


def get_rate_limit_stats():
    """Get current rate limiting statistics."""
    import time
    now = time.time()
    stats = {}
    
    for ip, timestamps in _rate_limits.items():
        active = [t for t in timestamps if now - t < WINDOW_SECONDS]
        if active:
            count = len(active)
            stats[ip] = {
                'count': count,
                'percent': min(100, int((count / MAX_REQUESTS) * 100))
            }
    
    return stats


def register_security_routes(app):
    """Register security dashboard routes on existing Flask app."""
    
    # Get auth settings from curator_app
    AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD', '')
    
    def check_auth(password):
        return password == AUTH_PASSWORD
    
    def authenticate():
        return Response(
            'Password required.',
            401,
            {'WWW-Authenticate': 'Basic realm="Security Dashboard"'}
        )
    
    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if AUTH_PASSWORD:
                auth = request.authorization
                if not auth or not check_auth(auth.password):
                    return authenticate()
            return f(*args, **kwargs)
        return decorated
    
    @app.route('/security')
    @requires_auth
    def security_dashboard():
        """Security monitoring dashboard."""
        rate_stats = get_rate_limit_stats()
        
        return render_template_string(
            SECURITY_TEMPLATE,
            auth_enabled=bool(AUTH_PASSWORD),
            max_requests=MAX_REQUESTS,
            active_ips=len(rate_stats),
            rate_stats=rate_stats,
            activity_logs=[]  # Could be populated from a log file
        )
    
    @app.route('/security/stats')
    @requires_auth
    def security_stats():
        """API endpoint for security stats."""
        rate_stats = get_rate_limit_stats()
        return jsonify({
            'active_ips': len(rate_stats),
            'rate_stats': rate_stats,
            'max_requests': MAX_REQUESTS,
            'window_seconds': WINDOW_SECONDS
        })
    
    return app
