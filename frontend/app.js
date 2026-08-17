// Initialize icons
lucide.createIcons();

// State
let resultsData = [];
let summaryData = null;
let verificationData = null;

// DOM Elements
const sections = document.querySelectorAll('.section');
const navLinks = document.querySelectorAll('.nav-links a');

// Navigation Logic
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = link.getAttribute('href').substring(1);
        
        // Update Nav
        navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        
        // Update Sections
        sections.forEach(s => s.classList.remove('active'));
        document.getElementById(targetId).classList.add('active');
    });
});

// Fetch Data
async function loadData() {
    try {
        const [res, sum, ver] = await Promise.all([
            fetch('./data/results.json').then(r => r.json()),
            fetch('./data/summary.json').then(r => r.json()),
            fetch('./data/verification.json').then(r => r.json())
        ]);
        
        resultsData = res;
        summaryData = sum;
        verificationData = ver;
        
        renderOverview();
        renderPatterns();
        renderMatrix(resultsData);
        renderVerification();
        
        lucide.createIcons();
    } catch (e) {
        console.error("Failed to load data:", e);
        document.getElementById('overview').innerHTML = `
            <div class="hero">
                <h1>Data Not Found</h1>
                <p>Please ensure you have run the research scripts and exported the data to frontend/data/</p>
            </div>
        `;
    }
}

// Render Overview
function renderOverview() {
    if (!summaryData) return;
    
    const statsContainer = document.getElementById('summary-stats');
    statsContainer.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Apps Evaluated</div>
            <div class="stat-value brand">${summaryData.total_researched}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Ready (Green)</div>
            <div class="stat-value green">${summaryData.green_count}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Already Covered</div>
            <div class="stat-value brand">${summaryData.covered_count}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Blocked (Red)</div>
            <div class="stat-value red">${summaryData.red_count}</div>
        </div>
    `;
}

// Render Patterns
function renderPatterns() {
    if (!summaryData || !summaryData.patterns) return;
    
    const container = document.getElementById('patterns-container');
    container.innerHTML = summaryData.patterns.map(pattern => `
        <div class="pattern-card">
            <p>${pattern}</p>
        </div>
    `).join('');
}

// Render Matrix
function renderMatrix(data) {
    const tbody = document.getElementById('matrix-body');
    
    tbody.innerHTML = data.map((app, index) => {
        const api = app.api || {};
        const auth = app.authentication || {};
        const mcp = app.mcp || {};
        const wh = app.webhooks || {};
        const rec = app.recommendation || {};
        
        const buildability = rec.buildability || 'UNKNOWN';
        let buildClass = buildability.toLowerCase();
        
        let priority = rec.priority || 'UNKNOWN';
        if (priority === 'COVERED') buildClass = 'primary';
        
        return `
            <tr>
                <td>
                    <div class="app-name">
                        ${app.app_name}
                    </div>
                    <div class="app-category">${app.category || 'Unknown'}</div>
                </td>
                <td>
                    <div>${api.api_available === 'yes' ? '<i data-lucide="check" class="text-green-500"></i> Yes' : api.api_available}</div>
                    <div class="code-text mt-1">${(api.api_types || []).join(', ')}</div>
                </td>
                <td>
                    <div>${auth.developer_access || 'unknown'}</div>
                    <div class="code-text mt-1">${(auth.auth_methods || []).join(', ')}</div>
                </td>
                <td>
                    <div>MCP: ${mcp.status || 'unknown'}</div>
                    <div class="mt-1">WH: ${wh.available || 'unknown'}</div>
                </td>
                <td>
                    <span class="status-pill ${buildClass}">${priority}</span>
                </td>
                <td>
                    <div class="text-sm">${rec.recommendation_reason || ''}</div>
                    <button class="view-evidence-btn mt-2" onclick="showEvidence(${index})">
                        <i data-lucide="search"></i> View Evidence
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    lucide.createIcons();
}

// Filtering & Searching
document.getElementById('search-input').addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;
    filterData(term, activeFilter);
});

document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        
        const activeFilter = e.target.dataset.filter;
        const term = document.getElementById('search-input').value.toLowerCase();
        filterData(term, activeFilter);
    });
});

function filterData(searchTerm, statusFilter) {
    const filtered = resultsData.filter(app => {
        const matchSearch = app.app_name.toLowerCase().includes(searchTerm) || 
                            (app.category || '').toLowerCase().includes(searchTerm);
        
        const buildability = (app.recommendation?.buildability || 'UNKNOWN').toUpperCase();
        const matchFilter = statusFilter === 'ALL' || buildability === statusFilter;
        
        return matchSearch && matchFilter;
    });
    
    renderMatrix(filtered);
}

// Verification Render
function renderVerification() {
    if (!verificationData) return;
    
    document.getElementById('audit-summary').innerHTML = `
        <div class="audit-score">${verificationData.accuracy || 'N/A'}</div>
        <div class="audit-meta">
            <p><strong>Agent Accuracy</strong> verified on a sample size of ${verificationData.sample_size}.</p>
            <p>${verificationData.hits} Hits, ${verificationData.misses} Misses.</p>
        </div>
    `;
    
    const tbody = document.getElementById('audit-body');
    tbody.innerHTML = (verificationData.details || []).map(d => `
        <tr>
            <td class="font-bold">${d.app}</td>
            <td>${d.agent_result}</td>
            <td>${d.verified_result}</td>
            <td>
                <span class="status-pill ${d.hit_miss === 'HIT' ? 'green' : 'red'}">${d.hit_miss}</span>
            </td>
            <td class="text-sm text-gray-400">${d.reason}</td>
        </tr>
    `).join('');
}

// Modal Logic
function showEvidence(index) {
    const app = resultsData[index];
    document.getElementById('modal-title').textContent = `Evidence: ${app.app_name}`;
    
    const evidence = app.evidence || [];
    
    if (evidence.length === 0) {
        document.getElementById('modal-body').innerHTML = '<p>No evidence collected.</p>';
    } else {
        document.getElementById('modal-body').innerHTML = evidence.map(e => `
            <div class="evidence-item">
                <div class="evidence-meta">
                    <span class="status-pill primary">${e.source_type || 'Unknown'}</span>
                    <a href="${e.source_url}" target="_blank" class="evidence-source">${e.source_url} <i data-lucide="external-link" style="width:12px;height:12px"></i></a>
                </div>
                <p>${e.evidence_excerpt || 'No excerpt available.'}</p>
            </div>
        `).join('');
    }
    
    lucide.createIcons();
    document.getElementById('evidence-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('evidence-modal').classList.remove('active');
}

// Close modal on click outside
window.addEventListener('click', (e) => {
    const modal = document.getElementById('evidence-modal');
    if (e.target === modal) {
        closeModal();
    }
});

async function runDemo() {
    const inputField = document.getElementById('demo-app-select');
    const appName = inputField.value.trim();
    if (!appName) {
        alert("Please enter an app name.");
        return;
    }
    
    const spinner = document.getElementById('demo-spinner');
    const resDiv = document.getElementById('demo-result');
    const btn = document.querySelector('button[onclick="runDemo()"]');

    spinner.classList.remove('hidden');
    resDiv.classList.add('hidden');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = "Researching...";
    }

    try {
        // For local development it remains localhost, but in production Vercel will run a build script to replace this
        const BACKEND_URL = '__API_URL__';
        const url = BACKEND_URL === '__API_URL__' ? 'http://localhost:8000' : BACKEND_URL;
        
        const response = await fetch(`${url}/research/${encodeURIComponent(appName)}`, { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            resDiv.innerHTML = `<pre style="white-space: pre-wrap; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #a5b4fc;">${JSON.stringify(data, null, 2)}</pre>`;
        } else {
            const errorText = await response.text();
            resDiv.innerHTML = `<p style="color: var(--red);">Error: ${errorText}</p>`;
        }
    } catch (e) {
        console.error("Live backend failed", e);
        resDiv.innerHTML = `<p style="color: var(--yellow);">Could not connect to the API. Make sure you run 'python server.py' to start the local backend!</p>`;
    }

    spinner.classList.add('hidden');
    resDiv.classList.remove('hidden');
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = "Research Live";
    }
}

// Initialize
loadData();
