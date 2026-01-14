# Kanban-style HTML template for Newsletter Curator
# Linear/Vercel/Raycast aesthetic redesign - January 2026
# Design: zinc-950 background, 1px borders, tight typography, ghost buttons

KANBAN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter Curator</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        /* ============================================
           LINEAR/VERCEL DESIGN SYSTEM
           ============================================ */
        :root {
            /* Zinc Palette */
            --bg-primary: #09090b;      /* zinc-950 */
            --bg-surface: #18181b;      /* zinc-900 */
            --bg-elevated: #27272a;     /* zinc-800 */
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-default: rgba(255, 255, 255, 0.1);
            --border-hover: rgba(255, 255, 255, 0.2);
            
            /* Text */
            --text-primary: #fafafa;    /* zinc-50 */
            --text-secondary: #a1a1aa;  /* zinc-400 */
            --text-muted: #71717a;      /* zinc-500 */
            
            /* Accent (subtle, not bright) */
            --accent-glow: rgba(99, 102, 241, 0.15);
            --accent-border: rgba(99, 102, 241, 0.5);
            
            /* Status */
            --success: #22c55e;
            --warning: #eab308;
            --error: #ef4444;
            --canadian: #dc2626;
            
            /* Typography */
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            --letter-spacing-tight: -0.02em;
            
            /* Spacing (high density) */
            --space-1: 4px;
            --space-2: 8px;
            --space-3: 12px;
            --space-4: 16px;
            --space-5: 20px;
            
            /* Border Radius */
            --radius-sm: 4px;
            --radius-md: 6px;
            --radius-lg: 8px;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: var(--font-sans);
            background: var(--bg-primary);
            min-height: 100vh;
            color: var(--text-primary);
            font-size: 13px;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }
        
        /* ============================================
           HEADER - Sticky top bar
           ============================================ */
        .header {
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border-subtle);
            padding: var(--space-3) var(--space-5);
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(12px);
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: var(--space-4);
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            font-size: 14px;
            font-weight: 600;
            letter-spacing: var(--letter-spacing-tight);
            color: var(--text-primary);
        }
        
        .logo-icon {
            font-size: 18px;
        }
        
        .header-nav {
            display: flex;
            gap: var(--space-1);
        }
        
        .nav-link {
            padding: var(--space-2) var(--space-3);
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            border-radius: var(--radius-sm);
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
        
        .header-actions {
            display: flex;
            gap: var(--space-2);
            align-items: center;
        }
        
        /* ============================================
           BUTTONS - Ghost/outlined style
           ============================================ */
        .btn {
            padding: 6px 12px;
            border: 1px solid var(--border-default);
            border-radius: var(--radius-md);
            font-weight: 500;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.15s ease;
            background: transparent;
            color: var(--text-secondary);
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-family: var(--font-sans);
        }
        
        .btn:hover {
            border-color: var(--border-hover);
            color: var(--text-primary);
            background: var(--accent-glow);
        }
        
        .btn:active {
            transform: scale(0.98);
        }
        
        .btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        
        .btn-primary {
            background: var(--accent-glow);
            border-color: var(--accent-border);
            color: var(--text-primary);
        }
        
        .btn-primary:hover {
            background: rgba(99, 102, 241, 0.25);
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
        }
        
        /* Search */
        .search-box {
            padding: 6px 12px;
            border: 1px solid var(--border-default);
            border-radius: var(--radius-md);
            background: var(--bg-surface);
            color: var(--text-primary);
            font-size: 12px;
            width: 200px;
            font-family: var(--font-sans);
            transition: all 0.15s ease;
        }
        
        .search-box::placeholder {
            color: var(--text-muted);
        }
        
        .search-box:focus {
            outline: none;
            border-color: var(--accent-border);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }
        
        /* ============================================
           KANBAN BOARD
           ============================================ */
        .kanban-container {
            display: flex;
            gap: var(--space-3);
            padding: var(--space-4);
            overflow-x: auto;
            min-height: calc(100vh - 130px);
        }
        
        .kanban-column {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            min-width: 280px;
            max-width: 300px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            max-height: calc(100vh - 170px);
        }
        
        .column-unsorted {
            min-width: 340px;
            max-width: 360px;
        }
        
        .column-header {
            padding: var(--space-3) var(--space-4);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .column-title {
            font-weight: 600;
            font-size: 12px;
            letter-spacing: var(--letter-spacing-tight);
            color: var(--text-primary);
            text-transform: uppercase;
        }
        
        .column-count {
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-muted);
            padding: 2px 8px;
            background: var(--bg-elevated);
            border-radius: var(--radius-sm);
        }
        
        .column-content {
            padding: var(--space-2);
            overflow-y: auto;
            flex: 1;
            min-height: 80px;
        }
        
        .column-content.drag-over {
            background: var(--accent-glow);
            box-shadow: inset 0 0 0 2px var(--accent-border);
            border-radius: var(--radius-md);
        }
        
        /* ============================================
           ARTICLE CARDS
           ============================================ */
        .article-card {
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: var(--space-3);
            margin-bottom: var(--space-2);
            cursor: grab;
            transition: all 0.15s ease;
        }
        
        .article-card:hover {
            border-color: var(--border-hover);
            background: #2e2e32;
        }
        
        .article-card.dragging {
            opacity: 0.5;
            cursor: grabbing;
        }
        
        .article-card.canadian {
            border-left: 2px solid var(--canadian);
        }
        
        .card-title {
            font-size: 12px;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: var(--space-2);
            line-height: 1.4;
            letter-spacing: var(--letter-spacing-tight);
        }
        
        .card-title a {
            color: var(--text-primary);
            text-decoration: none;
            transition: color 0.15s ease;
        }
        
        .card-title a:hover {
            color: #818cf8;
        }
        
        .card-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
        }
        
        .card-source {
            font-family: var(--font-mono);
            color: var(--text-muted);
            max-width: 140px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .card-badges {
            display: flex;
            gap: 4px;
        }
        
        /* Badges */
        .badge {
            padding: 2px 6px;
            border-radius: var(--radius-sm);
            font-family: var(--font-mono);
            font-size: 10px;
            font-weight: 500;
            border: 1px solid transparent;
        }
        
        .badge-score-high {
            color: var(--success);
            background: rgba(34, 197, 94, 0.1);
            border-color: rgba(34, 197, 94, 0.3);
        }
        
        .badge-score-med {
            color: var(--warning);
            background: rgba(234, 179, 8, 0.1);
            border-color: rgba(234, 179, 8, 0.3);
        }
        
        .badge-score-low {
            color: var(--text-muted);
            background: var(--bg-surface);
        }
        
        .badge-canadian {
            color: var(--canadian);
            background: rgba(220, 38, 38, 0.1);
            border-color: rgba(220, 38, 38, 0.3);
        }
        
        /* ============================================
           THEME SECTION (Collapsible footer)
           ============================================ */
        .theme-section {
            background: var(--bg-surface);
            border-top: 1px solid var(--border-subtle);
            padding: var(--space-3) var(--space-5);
        }
        
        .theme-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            padding: var(--space-2) 0;
        }
        
        .theme-header:hover {
            opacity: 0.8;
        }
        
        .theme-title {
            font-weight: 600;
            font-size: 12px;
            letter-spacing: var(--letter-spacing-tight);
            color: var(--text-primary);
            text-transform: uppercase;
        }
        
        .theme-toggle {
            color: var(--text-muted);
            font-size: 10px;
        }
        
        .theme-content {
            margin-top: var(--space-3);
            display: none;
        }
        
        .theme-content.expanded {
            display: block;
        }
        
        .theme-input {
            width: 100%;
            padding: var(--space-2) var(--space-3);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-md);
            background: var(--bg-elevated);
            color: var(--text-primary);
            font-size: 12px;
            font-family: var(--font-sans);
            margin-bottom: var(--space-2);
            transition: all 0.15s ease;
        }
        
        .theme-input:focus {
            outline: none;
            border-color: var(--accent-border);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }
        
        .theme-textarea {
            min-height: 70px;
            resize: vertical;
        }
        
        .theme-actions {
            display: flex;
            gap: var(--space-3);
            align-items: center;
            margin-top: var(--space-2);
        }
        
        .theme-actions label {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            font-size: 12px;
            color: var(--text-secondary);
            cursor: pointer;
        }
        
        /* ============================================
           STATUS BANNER (Toast notification)
           ============================================ */
        .status-banner {
            position: fixed;
            top: 70px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-elevated);
            border: 1px solid var(--border-default);
            color: var(--text-primary);
            padding: var(--space-3) var(--space-5);
            border-radius: var(--radius-lg);
            z-index: 9999;
            font-weight: 500;
            font-size: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            display: none;
            backdrop-filter: blur(8px);
        }
        
        .status-banner.visible {
            display: block;
            animation: slideIn 0.2s ease;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        
        /* Section color indicators */
        .section-indicator {
            width: 3px;
            height: 100%;
            position: absolute;
            left: 0;
            top: 0;
            border-radius: var(--radius-sm) 0 0 var(--radius-sm);
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: var(--border-default);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--border-hover);
        }
    </style>
</head>
<body>
    <div id="status-banner" class="status-banner"></div>
    
    <header class="header">
        <div class="header-left">
            <span class="logo">
                <span class="logo-icon">◆</span>
                Newsletter Curator
            </span>
            <nav class="header-nav">
                <a href="/" class="nav-link active">Curate</a>
                <a href="/security" class="nav-link">Security</a>
            </nav>
        </div>
        <div class="header-actions">
            <button class="btn" onclick="autoFillSections()" id="autofill-btn">
                <span>⚡</span> Auto-Fill
            </button>
            <button class="btn" onclick="scoreArticles()" id="score-btn">
                <span>◎</span> AI Score
            </button>
            <button class="btn btn-primary" onclick="generateNewsletter()">
                <span>→</span> Generate
            </button>
            <button class="btn" onclick="previewNewsletter()">
                <span>◈</span> Preview
            </button>
            <input type="text" class="search-box" placeholder="Search articles..." id="search-input" onkeyup="filterArticles()">
        </div>
    </header>
    
    <div class="kanban-container">
        <!-- Unsorted Articles Column -->
        <div class="kanban-column column-unsorted">
            <div class="column-header">
                <span class="column-title">Inbox</span>
                <span class="column-count" id="unsorted-count">{{ articles|length }}</span>
            </div>
            <div class="column-content" id="unsorted-column" ondrop="dropArticle(event, 'unsorted')" ondragover="allowDrop(event)" ondragleave="dragLeave(event)">
                {% for article in articles %}
                <div class="article-card {% if article._is_canadian %}canadian{% endif %}" 
                     draggable="true" 
                     ondragstart="dragStart(event)" 
                     id="card-{{ article._index }}"
                     data-index="{{ article._index }}"
                     data-title="{{ article.title }}"
                     data-source="{{ article.source }}">
                    <div class="card-title">
                        <a href="{{ article.link }}" target="_blank">{{ article.title[:75] }}{% if article.title|length > 75 %}...{% endif %}</a>
                    </div>
                    <div class="card-meta">
                        <span class="card-source">{{ article.source[:25] }}</span>
                        <div class="card-badges">
                            {% if article._is_canadian %}<span class="badge badge-canadian">CA</span>{% endif %}
                            <span class="badge badge-score-low" id="score-{{ article._index }}"></span>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- Section Columns -->
        {% for section in sections %}
        <div class="kanban-column" id="column-{{ section.id }}">
            <div class="column-header" style="border-left: 2px solid {{ section.color }};">
                <span class="column-title">{{ section.name }}</span>
                <span class="column-count" id="count-{{ section.id }}">0</span>
            </div>
            <div class="column-content" id="section-{{ section.id }}" ondrop="dropArticle(event, '{{ section.id }}')" ondragover="allowDrop(event)" ondragleave="dragLeave(event)">
            </div>
        </div>
        {% endfor %}
    </div>
    
    <div class="theme-section">
        <div class="theme-header" onclick="toggleTheme()">
            <span class="theme-title">Theme of the Week</span>
            <span class="theme-toggle" id="theme-toggle">▼</span>
        </div>
        <div class="theme-content" id="theme-content">
            <input type="text" class="theme-input" id="theme-title-input" placeholder="Theme title...">
            <textarea class="theme-input theme-textarea" id="theme-content-input" placeholder="Theme content..."></textarea>
            <div class="theme-actions">
                <label><input type="checkbox" id="theme-enabled"> Enable Theme</label>
                <button class="btn" onclick="generateTheme()">✨ AI Generate</button>
            </div>
        </div>
    </div>
    
    <script>
        const articles = {{ articles_json|safe }};
        let articleScores = {{ scores_json|safe }};
        const assignments = {};
        
        {% for section in sections %}
        assignments['{{ section.id }}'] = [];
        {% endfor %}
        
        let draggedCard = null;
        
        function dragStart(e) {
            draggedCard = e.target;
            e.target.classList.add('dragging');
            e.dataTransfer.setData('text/plain', e.target.dataset.index);
        }
        
        function allowDrop(e) {
            e.preventDefault();
            e.currentTarget.classList.add('drag-over');
        }
        
        function dragLeave(e) {
            e.currentTarget.classList.remove('drag-over');
        }
        
        function dropArticle(e, sectionId) {
            e.preventDefault();
            e.currentTarget.classList.remove('drag-over');
            
            const articleIndex = parseInt(e.dataTransfer.getData('text/plain'));
            const card = document.getElementById('card-' + articleIndex);
            
            if (!card) return;
            
            for (const [sid, indices] of Object.entries(assignments)) {
                const pos = indices.indexOf(articleIndex);
                if (pos > -1) {
                    indices.splice(pos, 1);
                    updateColumnCount(sid);
                }
            }
            
            if (sectionId !== 'unsorted') {
                assignments[sectionId].push(articleIndex);
            }
            
            e.currentTarget.appendChild(card);
            card.classList.remove('dragging');
            
            updateColumnCount(sectionId);
            updateUnsortedCount();
        }
        
        function updateColumnCount(sectionId) {
            const countEl = document.getElementById('count-' + sectionId);
            if (countEl && assignments[sectionId]) {
                countEl.textContent = assignments[sectionId].length;
            }
        }
        
        function updateUnsortedCount() {
            const unsortedCol = document.getElementById('unsorted-column');
            document.getElementById('unsorted-count').textContent = unsortedCol.children.length;
        }
        
        function filterArticles() {
            const query = document.getElementById('search-input').value.toLowerCase();
            document.querySelectorAll('.article-card').forEach(card => {
                const title = card.dataset.title.toLowerCase();
                const source = card.dataset.source.toLowerCase();
                card.style.display = (title.includes(query) || source.includes(query)) ? 'block' : 'none';
            });
        }
        
        function toggleTheme() {
            const content = document.getElementById('theme-content');
            const toggle = document.getElementById('theme-toggle');
            content.classList.toggle('expanded');
            toggle.textContent = content.classList.contains('expanded') ? '▲' : '▼';
        }
        
        function showStatus(msg) {
            const banner = document.getElementById('status-banner');
            banner.textContent = msg;
            banner.classList.add('visible');
        }
        
        function hideStatus() {
            document.getElementById('status-banner').classList.remove('visible');
        }
        
        function scoreArticles() {
            const btn = document.getElementById('score-btn');
            btn.disabled = true;
            btn.innerHTML = '<span>◎</span> Scoring...';
            showStatus('Scoring articles with AI...');
            
            fetch('/score', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(r => r.json())
            .then(data => {
                btn.disabled = false;
                btn.innerHTML = '<span>◎</span> AI Score';
                hideStatus();
                
                if (data.success) {
                    articleScores = {...articleScores, ...data.scores};
                    displayScores();
                    showStatus('✓ Scored ' + data.scored + ' articles');
                    setTimeout(hideStatus, 3000);
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }
        
        function displayScores() {
            Object.entries(articleScores).forEach(([idx, data]) => {
                const badge = document.getElementById('score-' + idx);
                if (badge && data.score) {
                    badge.textContent = data.score;
                    badge.className = 'badge ' + (data.score >= 7 ? 'badge-score-high' : data.score >= 4 ? 'badge-score-med' : 'badge-score-low');
                }
            });
        }
        
        function autoFillSections() {
            const sectionLimits = {
                'headlines': 5,
                'bright_spots': 2,
                'tools': 2,
                'deep_dives': 3,
                'grain_quality': 2,
                'learning': 2
            };
            
            const scored = Object.entries(articleScores)
                .map(([idx, data]) => ({idx: parseInt(idx), ...data}))
                .filter(a => a.score >= 4)
                .sort((a, b) => {
                    const aCanadian = articles[a.idx]?._is_canadian ? 10 : 0;
                    const bCanadian = articles[b.idx]?._is_canadian ? 10 : 0;
                    return (b.score + bCanadian) - (a.score + aCanadian);
                });
            
            const sectionCounts = {};
            for (const sid of Object.keys(sectionLimits)) {
                assignments[sid] = [];
                sectionCounts[sid] = 0;
                document.getElementById('section-' + sid).innerHTML = '';
            }
            
            for (const item of scored) {
                const section = item.section || 'headlines';
                const limit = sectionLimits[section] || 2;
                
                if (sectionCounts[section] < limit) {
                    const card = document.getElementById('card-' + item.idx);
                    if (card && card.parentElement.id === 'unsorted-column') {
                        assignments[section].push(item.idx);
                        document.getElementById('section-' + section).appendChild(card);
                        sectionCounts[section]++;
                    }
                }
            }
            
            for (const sid of Object.keys(sectionLimits)) {
                updateColumnCount(sid);
            }
            updateUnsortedCount();
            
            showStatus('✓ Auto-filled ' + Object.values(assignments).flat().length + ' articles');
            setTimeout(hideStatus, 3000);
        }
        
        function generateTheme() {
            showStatus('Generating Theme...');
            
            const selected = Object.values(assignments).flat();
            
            fetch('/generate-theme', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({article_indices: selected})
            })
            .then(r => r.json())
            .then(data => {
                hideStatus();
                if (data.success) {
                    document.getElementById('theme-title-input').value = data.title || '';
                    document.getElementById('theme-content-input').value = data.content || '';
                    document.getElementById('theme-enabled').checked = true;
                    document.getElementById('theme-content').classList.add('expanded');
                    document.getElementById('theme-toggle').textContent = '▲';
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }
        
        function generateNewsletter() {
            const theme = {
                title: document.getElementById('theme-title-input').value,
                content: document.getElementById('theme-content-input').value,
                enabled: document.getElementById('theme-enabled').checked
            };
            
            fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({assignments: assignments, theme: theme})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showStatus('✓ Newsletter generated');
                    setTimeout(() => {
                        hideStatus();
                        window.open('/preview', '_blank');
                    }, 1000);
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }
        
        function previewNewsletter() {
            window.open('/preview', '_blank');
        }
        
        async function autoCurate() {
            try {
                const scoredCount = Object.keys(articleScores).length;
                
                if (scoredCount < 50) {
                    showStatus('Scoring articles...');
                    
                    const scoreResponse = await fetch('/score', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'}
                    });
                    const scoreData = await scoreResponse.json();
                    
                    if (scoreData.success) {
                        articleScores = {...articleScores, ...scoreData.scores};
                        displayScores();
                    }
                }
                
                showStatus('Auto-filling sections...');
                await new Promise(r => setTimeout(r, 500));
                autoFillSections();
                
                const totalSelected = Object.values(assignments).flat().length;
                if (totalSelected > 0) {
                    showStatus('Generating Theme...');
                    
                    const themeResponse = await fetch('/generate-theme', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({article_indices: Object.values(assignments).flat()})
                    });
                    const themeData = await themeResponse.json();
                    
                    if (themeData.success) {
                        document.getElementById('theme-title-input').value = themeData.title || '';
                        document.getElementById('theme-content-input').value = themeData.content || '';
                        document.getElementById('theme-enabled').checked = true;
                    }
                }
                
                showStatus('✓ Ready to review');
                setTimeout(hideStatus, 3000);
                
            } catch (err) {
                showStatus('Error: ' + err.message);
                setTimeout(hideStatus, 5000);
            }
        }
        
        window.addEventListener('load', () => {
            displayScores();
            setTimeout(autoCurate, 1000);
        });
    </script>
</body>
</html>
'''
