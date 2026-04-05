"""
HTML Template Strings for BRAAS Drug Design Dashboard
=====================================================

This module provides HTML template strings for the drug design
web dashboard interface.

Author: BRAAS AI Pipeline Team
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any


# =============================================================================
# BASE TEMPLATE
# =============================================================================

BASE_TEMPLATE: str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - BRAAS Drug Design Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {{
            --braas-primary: #2c3e50;
            --braas-secondary: #3498db;
            --braas-accent: #27ae60;
            --braas-warning: #f39c12;
            --braas-danger: #e74c3c;
            --braas-light: #ecf0f1;
        }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: #f8f9fa;
        }}
        .navbar-brand {{
            font-weight: 700;
            color: var(--braas-primary) !important;
        }}
        .card {{
            border: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }}
        .card-header {{
            background: linear-gradient(135deg, var(--braas-primary), var(--braas-secondary));
            color: white;
            border-radius: 12px 12px 0 0 !important;
            font-weight: 600;
        }}
        .stat-card {{
            text-align: center;
            padding: 1.5rem;
        }}
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--braas-primary);
        }}
        .stat-label {{
            font-size: 0.9rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .pipeline-status {{
            height: 8px;
            border-radius: 4px;
            background: #e9ecef;
        }}
        .pipeline-progress {{
            height: 100%;
            border-radius: 4px;
            background: linear-gradient(90deg, var(--braas-secondary), var(--braas-accent));
            transition: width 0.5s ease;
        }}
        .nav-pills .nav-link {{
            color: var(--braas-primary);
            border-radius: 8px;
            margin: 0 4px;
        }}
        .nav-pills .nav-link.active {{
            background-color: var(--braas-secondary);
        }}
        .table-responsive {{
            border-radius: 8px;
            overflow: hidden;
        }}
        .badge-status {{
            font-size: 0.75rem;
            padding: 0.4em 0.8em;
        }}
        .chemical-structure {{
            background: white;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            min-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .chemical-structure svg {{
            max-width: 100%;
            height: auto;
        }}
        .alert-warning {{
            background-color: #fff3cd;
            border-color: #ffc107;
        }}
        .progress-indicator {{
            display: none;
        }}
        .progress-indicator.active {{
            display: block;
        }}
        .spinner-border-sm {{
            width: 1rem;
            height: 1rem;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div class="container-fluid">
            <a class="navbar-brand" href="/dashboard/">
                <i class="bi bi-droplet-fill text-primary me-2"></i>
                BRAAS Drug Design
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="nav nav-pills ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/dashboard/"><i class="bi bi-speedometer2 me-1"></i>Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/dashboard/drug-design"><i class="bi bi-kanban me-1"></i>Drug Design</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/dashboard/pipeline-status"><i class="bi bi-arrow-repeat me-1"></i>Pipeline</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/dashboard/results"><i class="bi bi-table me-1"></i>Results</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/knowledge/"><i class="bi bi-book me-1"></i>Knowledge</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        {content}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Polling for real-time updates
        function pollForUpdates(url, callback, interval) {{
            if (interval === undefined) interval = 5000;
            setInterval(function() {{
                fetch(url)
                    .then(function(response) {{ return response.json(); }})
                    .then(callback)
                    .catch(function(error) {{ console.error('Polling error:', error); }});
            }}, interval);
        }}
        
        // Submit discovery query
        async function submitDiscovery(formData) {{
            const response = await fetch('/dashboard/discover', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(Object.fromEntries(formData))
            }});
            return response.json();
        }}
        
        // Sort table by column
        function sortTable(tableId, column, direction) {{
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.sort(function(a, b) {{
                const aVal = a.cells[column].textContent.trim();
                const bVal = b.cells[column].textContent.trim();
                const cmp = isNaN(aVal) ? aVal.localeCompare(bVal) : parseFloat(aVal) - parseFloat(bVal);
                return direction === 'asc' ? cmp : -cmp;
            }});
            
            rows.forEach(function(row) {{ tbody.appendChild(row); }});
        }}
    </script>
</body>
</html>
"""


# =============================================================================
# MAIN DASHBOARD PAGE
# =============================================================================

DASHBOARD_TEMPLATE: str = """
<div class="row mb-4">
    <div class="col-12">
        <h2 class="mb-3"><i class="bi bi-speedometer2 me-2"></i>Drug Design Dashboard</h2>
        <p class="text-muted">Real-time monitoring and control of drug discovery pipelines</p>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card stat-card">
            <div class="stat-value">{active_experiments}</div>
            <div class="stat-label">Active Experiments</div>
            <i class="bi bi-flask text-primary mt-2" style="font-size: 2rem;"></i>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card stat-card">
            <div class="stat-value">{drug_candidates}</div>
            <div class="stat-label">Drug Candidates</div>
            <i class="bi bi-capsule text-success mt-2" style="font-size: 2rem;"></i>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card stat-card">
            <div class="stat-value">{compounds_tested}</div>
            <div class="stat-label">Compounds Tested</div>
            <i class="bi bi-snow text-info mt-2" style="font-size: 2rem;"></i>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card stat-card">
            <div class="stat-value">{pipeline_stage}</div>
            <div class="stat-label">Pipeline Stage</div>
            <i class="bi bi-diagram-3 text-warning mt-2" style="font-size: 2rem;"></i>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <i class="bi bi-arrow-repeat me-2"></i>Pipeline Progress
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span>Virtual Screening</span>
                        <span>{vs_progress}%</span>
                    </div>
                    <div class="pipeline-status">
                        <div class="pipeline-progress" style="width: {vs_progress}%"></div>
                    </div>
                </div>
                <div class="mb-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span>ADMET Prediction</span>
                        <span>{admet_progress}%</span>
                    </div>
                    <div class="pipeline-status">
                        <div class="pipeline-progress" style="width: {admet_progress}%"></div>
                    </div>
                </div>
                <div class="mb-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span>Molecular Dynamics</span>
                        <span>{md_progress}%</span>
                    </div>
                    <div class="pipeline-status">
                        <div class="pipeline-progress" style="width: {md_progress}%"></div>
                    </div>
                </div>
                <div>
                    <div class="d-flex justify-content-between mb-1">
                        <span>Lead Optimization</span>
                        <span>{lo_progress}%</span>
                    </div>
                    <div class="pipeline-status">
                        <div class="pipeline-progress" style="width: {lo_progress}%"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <i class="bi bi-exclamation-triangle me-2"></i>System Alerts
            </div>
            <div class="card-body">
                {alerts}
            </div>
        </div>
        
        <div class="card mt-3">
            <div class="card-header">
                <i class="bi bi-lightning me-2"></i>Quick Actions
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="/dashboard/drug-design" class="btn btn-primary">
                        <i class="bi bi-plus-circle me-2"></i>New Drug Discovery Query
                    </a>
                    <a href="/dashboard/pipeline-status" class="btn btn-outline-secondary">
                        <i class="bi bi-arrow-repeat me-2"></i>View Pipeline Details
                    </a>
                    <a href="/dashboard/results" class="btn btn-outline-success">
                        <i class="bi bi-table me-2"></i>Browse Results
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <i class="bi bi-clock-history me-2"></i>Recent Activity
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Timestamp</th>
                                <th>Event</th>
                                <th>Target</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recent_activity}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Auto-refresh dashboard data every 30 seconds
if (typeof pollForUpdates === 'function') {{
    pollForUpdates('/dashboard/api/status', function(data) {{
        // Update stats from API response
    }}, 30000);
}}
</script>
"""


# =============================================================================
# DRUG DESIGN PAGE
# =============================================================================

DRUG_DESIGN_TEMPLATE: str = """
<div class="row mb-4">
    <div class="col-12">
        <h2 class="mb-3"><i class="bi bi-kanban me-2"></i>Drug Design Workspace</h2>
        <p class="text-muted">Search targets, browse compound libraries, and analyze drug candidates</p>
    </div>
</div>

<div class="row">
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <i class="bi bi-search me-2"></i>Target/Disease Search
            </div>
            <div class="card-body">
                <form id="discoveryForm">
                    <div class="mb-3">
                        <label class="form-label">Target Gene/Protein</label>
                        <input type="text" class="form-control" name="target" placeholder="e.g., MSTN, myostatin, ALK4" value="{default_target}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Disease Area</label>
                        <select class="form-select" name="disease">
                            <option value="sarcopenia">Sarcopenia</option>
                            <option value="muscular_dystrophy">Muscular Dystrophy</option>
                            <option value="cachexia">Cancer Cachexia</option>
                            <option value="frailty">Geriatric Frailty</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Mechanism Class</label>
                        <select class="form-select" name="mechanism">
                            <option value="">Any</option>
                            <option value="antibody">Antibody</option>
                            <option value="small_molecule">Small Molecule</option>
                            <option value="gene_therapy">Gene Therapy</option>
                            <option value="kinase_inhibitor">Kinase Inhibitor</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Maximum Results</label>
                        <input type="number" class="form-control" name="max_results" value="50" min="10" max="500">
                    </div>
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="bi bi-search me-2"></i>Run Discovery
                    </button>
                </form>
                
                <div class="progress-indicator mt-3" id="progressIndicator">
                    <div class="d-flex align-items-center">
                        <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                        <span>Processing discovery query...</span>
                    </div>
                    <div class="progress mt-2" style="height: 6px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card mt-3">
            <div class="card-header">
                <i class="bi bi-collection me-2"></i>Compound Library
            </div>
            <div class="card-body p-0">
                <div class="list-group list-group-flush">
                    <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-database me-2"></i>Approved Drugs</span>
                        <span class="badge bg-primary rounded-pill">{approved_count}</span>
                    </a>
                    <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-hourglass-split me-2"></i>Clinical Trials</span>
                        <span class="badge bg-info rounded-pill">{clinical_count}</span>
                    </a>
                    <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-beaker me-2"></i>Preclinical</span>
                        <span class="badge bg-warning rounded-pill">{preclinical_count}</span>
                    </a>
                    <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-flower1 me-2"></i>Natural Products</span>
                        <span class="badge bg-success rounded-pill">{natural_count}</span>
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-8">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span><i class="bi bi-table me-2"></i>Drug Candidates</span>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-light btn-sm" onclick="sortResults('name')">Sort by Name</button>
                    <button class="btn btn-outline-light btn-sm" onclick="sortResults('stage')">Sort by Stage</button>
                    <button class="btn btn-outline-light btn-sm" onclick="sortResults('company')">Sort by Company</button>
                </div>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0" id="candidatesTable">
                        <thead class="table-light">
                            <tr>
                                <th>Compound</th>
                                <th>Company</th>
                                <th>Mechanism</th>
                                <th>Stage</th>
                                <th>Status</th>
                                <th>Key Data</th>
                            </tr>
                        </thead>
                        <tbody id="candidatesTableBody">
                            {candidates_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="card mt-3">
            <div class="card-header">
                <i class="bi bi-diagram-2 me-2"></i>Chemical Structure Viewer
            </div>
            <div class="card-body">
                <div class="chemical-structure" id="structureViewer">
                    <svg width="300" height="200" viewBox="0 0 300 200">
                        <rect fill="#f8f9fa" width="100%" height="100%"/>
                        <text x="150" y="100" text-anchor="middle" fill="#6c757d" font-size="14">
                            Select a compound to view structure
                        </text>
                    </svg>
                </div>
                <div class="mt-3 text-center">
                    <button class="btn btn-sm btn-outline-primary" onclick="loadStructure()">
                        <i class="bi bi-arrow-clockwise me-1"></i>Load Structure
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="downloadStructure()">
                        <i class="bi bi-download me-1"></i>Download SDF
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.getElementById('discoveryForm').addEventListener('submit', async function(e) {{
    e.preventDefault();
    const formData = new FormData(this);
    const indicator = document.getElementById('progressIndicator');
    
    indicator.classList.add('active');
    
    try {{
        const result = await submitDiscovery(formData);
        if (result.success) {{
            location.reload();
        }} else {{
            alert('Discovery query failed: ' + result.error);
        }}
    }} catch (error) {{
        alert('Error: ' + error.message);
    }} finally {{
        indicator.classList.remove('active');
    }}
}});

async function loadCandidates() {{
    try {{
        const response = await fetch('/dashboard/api/candidates');
        const data = await response.json();
        updateCandidatesTable(data.candidates);
    }} catch (error) {{
        console.error('Failed to load candidates:', error);
    }}
}}

function updateCandidatesTable(candidates) {{
    const tbody = document.getElementById('candidatesTableBody');
    if (tbody && candidates) {{
        tbody.innerHTML = candidates.map(function(c) {{
            return '<tr onclick="selectCompound(\\'' + c.name + '\\')" style="cursor: pointer;">' +
                '<td><strong>' + c.name + '</strong></td>' +
                '<td>' + c.company + '</td>' +
                '<td><small>' + c.mechanism + '</small></td>' +
                '<td><span class="badge bg-secondary">' + (c.stage || 'N/A') + '</span></td>' +
                '<td><span class="badge ' + getStatusClass(c.status) + '">' + (c.status || 'Unknown') + '</span></td>' +
                '<td><small>' + (c.key_data || 'N/A') + '</small></td>' +
                '</tr>';
        }}).join('');
    }}
}}

function getStatusClass(status) {{
    var classes = {{
        'Active': 'bg-success',
        'Phase 3': 'bg-primary',
        'Phase 2': 'bg-info',
        'Discontinued': 'bg-danger',
        'Approved': 'bg-success'
    }};
    return classes[status] || 'bg-secondary';
}}

function selectCompound(name) {{
    document.getElementById('structureViewer').innerHTML = 
        '<svg width="300" height="200" viewBox="0 0 300 200">' +
        '<rect fill="#e8f4f8" width="100%" height="100%"/>' +
        '<text x="150" y="90" text-anchor="middle" fill="#2c3e50" font-size="12" font-weight="bold">' + name + '</text>' +
        '<text x="150" y="110" text-anchor="middle" fill="#6c757d" font-size="10">Structure loading...</text>' +
        '</svg>';
}}

function sortResults(column) {{
    // Sorting implementation
}}

function loadStructure() {{
    // Load chemical structure
}}

function downloadStructure() {{
    // Download structure as SDF
}}

// Initial load
if (typeof loadCandidates === 'function') {{
    loadCandidates();
}}
</script>
"""


# =============================================================================
# PIPELINE STATUS PAGE
# =============================================================================

PIPELINE_STATUS_TEMPLATE: str = """
<div class="row mb-4">
    <div class="col-12">
        <h2 class="mb-3"><i class="bi bi-arrow-repeat me-2"></i>Pipeline Status</h2>
        <p class="text-muted">Real-time monitoring of drug discovery pipeline stages</p>
    </div>
</div>

<div class="row">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                <i class="bi bi-list-check me-2"></i>Pipeline Stages
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Stage</th>
                                <th>Status</th>
                                <th>Progress</th>
                                <th>Duration</th>
                                <th>Results</th>
                            </tr>
                        </thead>
                        <tbody>
                            {pipeline_stages}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <i class="bi bi-gpu me-2"></i>Compute Resources
            </div>
            <div class="card-body">
                <div class="row text-center">
                    <div class="col-6">
                        <div class="stat-value">{cpu_usage}%</div>
                        <div class="stat-label">CPU Usage</div>
                    </div>
                    <div class="col-6">
                        <div class="stat-value">{memory_usage}%</div>
                        <div class="stat-label">Memory Usage</div>
                    </div>
                </div>
                <hr>
                <div class="row text-center">
                    <div class="col-4">
                        <div class="stat-value">{gpu_available}</div>
                        <div class="stat-label">GPUs Available</div>
                    </div>
                    <div class="col-4">
                        <div class="stat-value">{jobs_queued}</div>
                        <div class="stat-label">Jobs Queued</div>
                    </div>
                    <div class="col-4">
                        <div class="stat-value">{jobs_running}</div>
                        <div class="stat-label">Jobs Running</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <i class="bi bi-terminal me-2"></i>Active Jobs
            </div>
            <div class="card-body p-0">
                <div class="list-group list-group-flush" id="activeJobsList">
                    {active_jobs}
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Poll for pipeline updates every 10 seconds
if (typeof pollForUpdates === 'function') {{
    pollForUpdates('/dashboard/api/pipeline', function(data) {{
        updatePipelineDisplay(data);
    }}, 10000);
}}

function updatePipelineDisplay(data) {{
    // Update pipeline stages table
    // Update compute resources
    // Update active jobs
}}
</script>
"""


# =============================================================================
# RESULTS PAGE
# =============================================================================

RESULTS_TEMPLATE: str = """
<div class="row mb-4">
    <div class="col-12">
        <h2 class="mb-3"><i class="bi bi-table me-2"></i>Drug Candidate Results</h2>
        <p class="text-muted">Browse and analyze drug discovery results</p>
    </div>
</div>

<div class="row mb-3">
    <div class="col-md-12">
        <div class="card">
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <label class="form-label">Filter by Target</label>
                        <select class="form-select" id="targetFilter">
                            <option value="">All Targets</option>
                            <option value="MSTN">Myostatin (MSTN)</option>
                            <option value="ALK4">ALK4</option>
                            <option value="ActRIIB">ActRIIB</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label">Filter by Stage</label>
                        <select class="form-select" id="stageFilter">
                            <option value="">All Stages</option>
                            <option value="Approved">Approved</option>
                            <option value="Phase 3">Phase 3</option>
                            <option value="Phase 2">Phase 2</option>
                            <option value="Phase 1">Phase 1</option>
                            <option value="Preclinical">Preclinical</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label">Sort By</label>
                        <select class="form-select" id="sortBy">
                            <option value="rank">Rank</option>
                            <option value="company">Company</option>
                            <option value="stage">Stage</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span><i class="bi bi-collection me-2"></i>Results ({total_results} candidates)</span>
                <div>
                    <button class="btn btn-sm btn-outline-primary me-2" onclick="exportCSV()">
                        <i class="bi bi-file-earmark-arrow-down me-1"></i>Export CSV
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="exportJSON()">
                        <i class="bi bi-file-earmark-code me-1"></i>Export JSON
                    </button>
                </div>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0" id="resultsTable">
                        <thead class="table-light">
                            <tr>
                                <th>Rank</th>
                                <th>Compound</th>
                                <th>Company</th>
                                <th>Mechanism</th>
                                <th>Stage</th>
                                <th>Status</th>
                                <th>Key Data</th>
                                <th>Differentiation</th>
                            </tr>
                        </thead>
                        <tbody id="resultsTableBody">
                            {results_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="card-footer">
                <nav>
                    <ul class="pagination justify-content-center mb-0" id="pagination">
                        {pagination}
                    </ul>
                </nav>
            </div>
        </div>
    </div>
</div>

<script>
var currentResults = [];

async function loadResults() {{
    try {{
        var response = await fetch('/dashboard/api/candidates');
        currentResults = await response.json();
        renderResults(currentResults);
    }} catch (error) {{
        console.error('Failed to load results:', error);
    }}
}}

function renderResults(results) {{
    var tbody = document.getElementById('resultsTableBody');
    if (tbody && results) {{
        tbody.innerHTML = results.map(function(r) {{
            return '<tr>' +
                '<td><strong>' + (r.rank || '-') + '</strong></td>' +
                '<td><strong>' + r.name + '</strong></td>' +
                '<td>' + r.company + '</td>' +
                '<td><small>' + r.mechanism + '</small></td>' +
                '<td><span class="badge bg-secondary">' + (r.stage || 'N/A') + '</span></td>' +
                '<td><span class="badge ' + getStatusClass(r.status) + '">' + (r.status || 'Unknown') + '</span></td>' +
                '<td><small>' + (r.key_data || 'N/A') + '</small></td>' +
                '<td><small>' + (r.differentiation || 'N/A') + '</small></td>' +
                '</tr>';
        }}).join('');
    }}
}}

function getStatusClass(status) {{
    var classes = {{
        'Active': 'bg-success',
        'Phase 3': 'bg-primary',
        'Phase 2': 'bg-info',
        'Discontinued': 'bg-danger',
        'Approved': 'bg-success'
    }};
    return classes[status] || 'bg-secondary';
}}

function exportCSV() {{
    var rows = [['Rank', 'Compound', 'Company', 'Mechanism', 'Stage', 'Status', 'Key Data', 'Differentiation']];
    currentResults.forEach(function(r) {{
        rows.push([r.rank || '', r.name || '', r.company || '', r.mechanism || '', r.stage || '', r.status || '', r.key_data || '', r.differentiation || '']);
    }});
    
    var csv = rows.map(function(row) {{ return row.map(function(cell) {{ return '"' + cell + '"'; }}).join(','); }}).join('\\n');
    var blob = new Blob([csv], {{ type: 'text/csv' }});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'drug_candidates.csv';
    a.click();
}}

function exportJSON() {{
    var blob = new Blob([JSON.stringify(currentResults, null, 2)], {{ type: 'application/json' }});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'drug_candidates.json';
    a.click();
}}

// Initial load
loadResults();
</script>
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_default_dashboard_context() -> Dict[str, Any]:
    """Returns default context for dashboard page."""
    return {
        "title": "Main Dashboard",
        "active_experiments": 3,
        "drug_candidates": 47,
        "compounds_tested": 1284,
        "pipeline_stage": "Lead Optimization",
        "vs_progress": 100,
        "admet_progress": 75,
        "md_progress": 50,
        "lo_progress": 25,
        "alerts": """
            <div class="alert alert-warning mb-2" role="alert">
                <i class="bi bi-exclamation-triangle me-2"></i>
                <strong>Low memory warning:</strong> GPU cluster at 85% capacity
            </div>
            <div class="alert alert-info mb-2" role="alert">
                <i class="bi bi-info-circle me-2"></i>
                New compounds added to natural products library
            </div>
        """,
        "recent_activity": """
            <tr>
                <td>2026-04-05 21:30</td>
                <td>Virtual screening completed</td>
                <td>MSTN</td>
                <td><span class="badge bg-success">Complete</span></td>
            </tr>
            <tr>
                <td>2026-04-05 21:25</td>
                <td>ADMET prediction started</td>
                <td>ALK4</td>
                <td><span class="badge bg-info">Running</span></td>
            </tr>
            <tr>
                <td>2026-04-05 21:20</td>
                <td>Molecular dynamics initiated</td>
                <td>MSTN</td>
                <td><span class="badge bg-info">Running</span></td>
            </tr>
        """
    }


def get_default_drug_design_context() -> Dict[str, Any]:
    """Returns default context for drug design page."""
    return {
        "title": "Drug Design",
        "default_target": "MSTN",
        "approved_count": 1,
        "clinical_count": 8,
        "preclinical_count": 12,
        "natural_count": 45,
        "candidates_rows": """
            <tr onclick="selectCompound('Apitegromab')" style="cursor: pointer;">
                <td><strong>Apitegromab</strong></td>
                <td>Scholar Rock</td>
                <td><small>Anti-propeptide antibody</small></td>
                <td><span class="badge bg-primary">Phase 3</span></td>
                <td><span class="badge bg-success">Active</span></td>
                <td><small>TOPAZA: +22.6m 6MWT</small></td>
            </tr>
            <tr onclick="selectCompound('Bimagrumab')" style="cursor: pointer;">
                <td><strong>Bimagrumab</strong></td>
                <td>MediGene</td>
                <td><small>ActRIIA/B blocker</small></td>
                <td><span class="badge bg-info">Phase 2</span></td>
                <td><span class="badge bg-success">Active</span></td>
                <td><small>+10.8% LBM, +31.8m 6MWT</small></td>
            </tr>
            <tr onclick="selectCompound('LY2495655')" style="cursor: pointer;">
                <td><strong>LY2495655</strong></td>
                <td>Eli Lilly</td>
                <td><small>Anti-myostatin antibody</small></td>
                <td><span class="badge bg-info">Phase 2</span></td>
                <td><span class="badge bg-success">Active</span></td>
                <td><small>+0.98kg appendicular LBM</small></td>
            </tr>
        """
    }


def get_default_pipeline_context() -> Dict[str, Any]:
    """Returns default context for pipeline status page."""
    return {
        "title": "Pipeline Status",
        "pipeline_stages": """
            <tr>
                <td><i class="bi bi-search me-2 text-primary"></i>Target Validation</td>
                <td><span class="badge bg-success">Complete</span></td>
                <td><div class="progress m-1" style="height: 6px;"><div class="progress-bar bg-success" style="width: 100%"></div></div></td>
                <td>2 hours</td>
                <td><a href="#">View</a></td>
            </tr>
            <tr>
                <td><i class="bi bi-virus me-2 text-info"></i>Virtual Screening</td>
                <td><span class="badge bg-success">Complete</span></td>
                <td><div class="progress m-1" style="height: 6px;"><div class="progress-bar bg-success" style="width: 100%"></div></div></td>
                <td>4 hours</td>
                <td><a href="#">View</a></td>
            </tr>
            <tr>
                <td><i class="bi bi-shield-check me-2 text-warning"></i>ADMET Prediction</td>
                <td><span class="badge bg-info">Running</span></td>
                <td><div class="progress m-1" style="height: 6px;"><div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 75%"></div></div></td>
                <td>1.5 hours (est.)</td>
                <td><a href="#">View</a></td>
            </tr>
            <tr>
                <td><i class="bi bi-wind me-2 text-secondary"></i>Molecular Dynamics</td>
                <td><span class="badge bg-warning">Queued</span></td>
                <td><div class="progress m-1" style="height: 6px;"><div class="progress-bar bg-secondary" style="width: 0%"></div></div></td>
                <td>Pending</td>
                <td><a href="#">View</a></td>
            </tr>
            <tr>
                <td><i class="bi bi-pencil-square me-2 text-secondary"></i>Lead Optimization</td>
                <td><span class="badge bg-secondary">Pending</span></td>
                <td><div class="progress m-1" style="height: 6px;"><div class="progress-bar bg-secondary" style="width: 0%"></div></div></td>
                <td>Pending</td>
                <td><a href="#">View</a></td>
            </tr>
        """,
        "cpu_usage": 72,
        "memory_usage": 68,
        "gpu_available": 4,
        "jobs_queued": 12,
        "jobs_running": 3,
        "active_jobs": """
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">ADMET Prediction Batch #47</h6>
                    <small class="text-muted">Running</small>
                </div>
                <p class="mb-1"><small>284 compounds | ETA: 1.5 hours</small></p>
                <div class="progress mt-2" style="height: 4px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated bg-info" style="width: 75%"></div>
                </div>
            </div>
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">Molecular Dynamics Batch #23</h6>
                    <small class="text-muted">Running</small>
                </div>
                <p class="mb-1"><small>12 complexes | ETA: 3 hours</small></p>
                <div class="progress mt-2" style="height: 4px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" style="width: 50%"></div>
                </div>
            </div>
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">Lead Optimization Query #12</h6>
                    <small class="text-muted">Running</small>
                </div>
                <p class="mb-1"><small>3 candidates | ETA: 30 min</small></p>
                <div class="progress mt-2" style="height: 4px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated bg-success" style="width: 85%"></div>
                </div>
            </div>
        """
    }


def get_default_results_context() -> Dict[str, Any]:
    """Returns default context for results page."""
    return {
        "title": "Results",
        "total_results": 9,
        "results_rows": """
            <tr>
                <td><strong>1</strong></td>
                <td><strong>Apitegromab</strong></td>
                <td>Scholar Rock</td>
                <td><small>Anti-propeptide antibody</small></td>
                <td><span class="badge bg-primary">Phase 3</span></td>
                <td><span class="badge bg-success">Active</span></td>
                <td><small>TOPAZA: +22.6m 6MWT</small></td>
                <td><small>Novel mechanism</small></td>
            </tr>
            <tr>
                <td><strong>2</strong></td>
                <td><strong>Bimagrumab</strong></td>
                <td>MediGene</td>
                <td><small>ActRIIA/B blocker</small></td>
                <td><span class="badge bg-info">Phase 2</span></td>
                <td><span class="badge bg-success">Active</span></td>
                <td><small>+10.8% LBM, +31.8m 6MWT</small></td>
                <td><small>Dual ligand blocking</small></td>
            </tr>
            <tr>
                <td><strong>3</strong></td>
                <td><strong>LY2495655</strong></td>
                <td>Eli Lilly</td>
                <td><small>Anti-myostatin antibody</small></td>
                <td><span class="badge bg-info">Phase 2</span></td>
                <td><span class="badge bg-success">Active</span></td>
                <td><small>+0.98kg appendicular LBM</small></td>
                <td><small>Oncology focus</small></td>
            </tr>
        """,
        "pagination": """
            <li class="page-item active"><a class="page-link" href="#">1</a></li>
            <li class="page-item"><a class="page-link" href="#">2</a></li>
            <li class="page-item"><a class="page-link" href="#">3</a></li>
        """
    }


def render_template(template: str, context: Dict[str, Any]) -> str:
    """Render a template with the given context dictionary."""
    return template.format(**context)


def get_full_page(title: str, content: str) -> str:
    """Get a full HTML page with the base template applied."""
    context = {"title": title, "content": content}
    return BASE_TEMPLATE.format(**context)
