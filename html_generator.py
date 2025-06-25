import json
from datetime import datetime
from typing import List, Dict, Any

def generate_html_report(api_calls: List[Dict[str, Any]], filename: str = 'api_calls_report.html') -> str:
    """Generate HTML report from API calls data"""
    # Calculate statistics
    total_calls = len(api_calls)
    successful_calls = len([call for call in api_calls if 200 <= call['status'] < 300])
    error_calls = len([call for call in api_calls if call['status'] >= 400])
    
    # Group by status codes and methods
    status_counts = {}
    method_counts = {'GET': 0, 'POST': 0, 'PUT': 0, 'DELETE': 0, 'PATCH': 0, 'OPTIONS': 0, 'HEAD': 0}
    for call in api_calls:
        status_counts[call['status']] = status_counts.get(call['status'], 0) + 1
        method = call['method'].upper()
        if method in method_counts:
            method_counts[method] += 1
        else:
            method_counts[method] = 1
    
    # Create JSON data for JavaScript
    api_calls_json = json.dumps(api_calls, indent=2)
    
    # Fix the line that referenced self.api_calls
    other_calls = total_calls - successful_calls - error_calls
    
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Calls Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .success {{ color: #27ae60; }}
        .error {{ color: #e74c3c; }}
        .total {{ color: #3498db; }}
        .warning {{ color: #f39c12; }}
        
        .controls {{
            padding: 20px 30px;
            background: white;
            border-bottom: 1px solid #eee;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .filter-group label {{
            font-weight: 500;
            color: #555;
        }}
        
        select, input {{
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }}
        
        select:focus, input:focus {{
            outline: none;
            border-color: #3498db;
        }}
        
        .api-table-container {{
            padding: 30px;
            overflow-x: auto;
        }}
        
        .api-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .api-table th {{
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 500;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .api-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }}
        
        .api-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .method-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .method-get {{ background: #e8f5e8; color: #2e7d2e; }}
        .method-post {{ background: #fff3cd; color: #856404; }}
        .method-put {{ background: #cce5ff; color: #004085; }}
        .method-delete {{ background: #f8d7da; color: #721c24; }}
        .method-patch {{ background: #e2e3e5; color: #383d41; }}
        
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        
        .status-2xx {{ background: #d4edda; color: #155724; }}
        .status-3xx {{ background: #cce5ff; color: #004085; }}
        .status-4xx {{ background: #f8d7da; color: #721c24; }}
        .status-5xx {{ background: #f5c6cb; color: #721c24; }}
        
        .url-cell {{
            max-width: 300px;
            word-break: break-all;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }}
        
        .response-preview {{
            max-width: 200px;
            max-height: 100px;
            overflow: hidden;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            background: #f8f9fa;
            padding: 5px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}
        
        .expand-btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
        }}
        
        .expand-btn:hover {{
            background: #0056b3;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }}
        
        .modal-content {{
            background-color: white;
            margin: 5% auto;
            padding: 20px;
            border-radius: 10px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }}
        
        .close {{
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }}
        
        .close:hover {{
            color: black;
        }}
        
        .json-viewer {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
        }}
        
        @media (max-width: 768px) {{
            .controls {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .filter-group {{
                justify-content: space-between;
            }}
            
            .api-table {{
                font-size: 12px;
            }}
            
            .api-table th, .api-table td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 API Calls Report</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number total">{total_calls}</div>
                <div class="stat-label">Total Calls</div>
            </div>
            <div class="stat-card">
                <div class="stat-number success">{successful_calls}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{error_calls}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning">{other_calls}</div>
                <div class="stat-label">Other</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="filter-group">
                <label for="methodFilter">Method:</label>
                <select id="methodFilter">
                    <option value="">All Methods</option>
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                    <option value="PATCH">PATCH</option>
                    <option value="OPTIONS">OPTIONS</option>
                    <option value="HEAD">HEAD</option>
                    {''.join([f'<option value="{method}">{method}</option>' for method in sorted(method_counts.keys()) if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']])}
                </select>
            </div>
            
            <div class="filter-group">
                <label for="statusFilter">Status:</label>
                <select id="statusFilter">
                    <option value="">All Status</option>
                    {''.join([f'<option value="{status}">{status}</option>' for status in sorted(status_counts.keys())])}
                </select>
            </div>
            
            <div class="filter-group">
                <label for="urlFilter">URL Contains:</label>
                <input type="text" id="urlFilter" placeholder="Filter by URL...">
            </div>
        </div>
        
        <div class="api-table-container">
            <table class="api-table" id="apiTable">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Method</th>
                        <th>URL</th>
                        <th>Status</th>
                        <th>Content Type</th>
                        <th>Response Preview</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="apiTableBody">
                    <!-- Table rows will be populated by JavaScript -->
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Modal for detailed view -->
    <div id="detailModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>API Call Details</h2>
            <div id="modalContent"></div>
        </div>
    </div>
    
    <script>
        // API calls data
        const apiCalls = {api_calls_json};
        let filteredCalls = [...apiCalls];
        
        // DOM elements
        const methodFilter = document.getElementById('methodFilter');
        const statusFilter = document.getElementById('statusFilter');
        const urlFilter = document.getElementById('urlFilter');
        const tableBody = document.getElementById('apiTableBody');
        const modal = document.getElementById('detailModal');
        const modalContent = document.getElementById('modalContent');
        const closeModal = document.querySelector('.close');
        
        // Event listeners
        methodFilter.addEventListener('change', applyFilters);
        statusFilter.addEventListener('change', applyFilters);
        urlFilter.addEventListener('input', applyFilters);
        closeModal.addEventListener('click', () => modal.style.display = 'none');
        window.addEventListener('click', (e) => {{
            if (e.target === modal) modal.style.display = 'none';
        }});
        
        // Apply filters
        function applyFilters() {{
            const methodValue = methodFilter.value;
            const statusValue = statusFilter.value;
            const urlValue = urlFilter.value.toLowerCase();
            
            filteredCalls = apiCalls.filter(call => {{
                const methodMatch = !methodValue || call.method === methodValue;
                const statusMatch = !statusValue || call.status.toString() === statusValue;
                const urlMatch = !urlValue || call.url.toLowerCase().includes(urlValue);
                
                return methodMatch && statusMatch && urlMatch;
            }});
            
            renderTable();
        }}
        
        // Render table
        function renderTable() {{
            tableBody.innerHTML = '';
            
            filteredCalls.forEach((call, index) => {{
                const row = document.createElement('tr');
                
                const timestamp = new Date(call.timestamp).toLocaleString();
                const methodClass = `method-${{call.method.toLowerCase()}}`;
                const statusClass = `status-${{Math.floor(call.status / 100)}}xx`;
                const responsePreview = call.responseBody ? 
                    call.responseBody.substring(0, 100) + (call.responseBody.length > 100 ? '...' : '') : 
                    'No content';
                
                row.innerHTML = `
                    <td>${{timestamp}}</td>
                    <td><span class="method-badge ${{methodClass}}">${{call.method}}</span></td>
                    <td class="url-cell">${{call.url}}</td>
                    <td><span class="status-badge ${{statusClass}}">${{call.status}} ${{call.statusText}}</span></td>
                    <td>${{call.mimeType}}</td>
                    <td class="response-preview">${{responsePreview}}</td>
                    <td><button class="expand-btn" onclick="showDetails(${{index}})">View Details</button></td>
                `;
                
                tableBody.appendChild(row);
            }});
        }}
        
        // Show detailed view
        function showDetails(index) {{
            const call = filteredCalls[index];
            const details = `
                <h3>Request Details</h3>
                <p><strong>Method:</strong> ${{call.method}}</p>
                <p><strong>URL:</strong> ${{call.url}}</p>
                <p><strong>Timestamp:</strong> ${{new Date(call.timestamp).toLocaleString()}}</p>
                <p><strong>Request ID:</strong> ${{call.requestId}}</p>
                
                ${{call.requestData ? `
                <h3>Request Data</h3>
                <div class="json-viewer">${{call.requestData}}</div>
                ` : ''}}
                
                ${{call.requestHeaders && Object.keys(call.requestHeaders).length > 0 ? `
                <h3>Request Headers</h3>
                <div class="json-viewer">${{JSON.stringify(call.requestHeaders, null, 2)}}</div>
                ` : ''}}
                
                <h3>Response Details</h3>
                <p><strong>Status:</strong> ${{call.status}} ${{call.statusText}}</p>
                <p><strong>Content Type:</strong> ${{call.mimeType}}</p>
                
                <h3>Response Headers</h3>
                <div class="json-viewer">${{JSON.stringify(call.headers, null, 2)}}</div>
                
                <h3>Response Body</h3>
                <div class="json-viewer">${{call.responseBody || 'No content'}}</div>
            `;
            
            modalContent.innerHTML = details;
            modal.style.display = 'block';
        }}
        
        // Initial render
        renderTable();
    </script>
</body>
</html>
    """
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
        return filename
    except Exception as e:
        raise Exception(f"Error generating HTML report: {e}")
