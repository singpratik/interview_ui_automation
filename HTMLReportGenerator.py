import json
import os
import logging
from datetime import datetime
import html

# Configure logging
logger = logging.getLogger(__name__)

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

class HTMLReportGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_calls = []
    
    def generate_report(self, api_calls, filename='api_calls_report.html'):
        """Generate a comprehensive HTML report of all API calls"""
        try:
            self.api_calls = api_calls  # Store API calls for later use
            abs_path = os.path.abspath(filename)
            logger.info(f"Generating report to: {abs_path}")
            logger.info(f"API calls count: {len(api_calls)}")
            
            html_content = self._create_html_report()
            
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                f.flush()  # Force immediate write
                os.fsync(f.fileno())  # Ensure OS buffer flush
                logger.debug("File write completed")
            
            # Verify file creation
            if os.path.exists(abs_path):
                file_size = os.path.getsize(abs_path)
                logger.info(f"✅ HTML report created: {abs_path} ({file_size} bytes)")
                return True
            else:
                logger.error(f"❌ File creation failed: {abs_path}")
                return False
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            return False
    
    def _sanitize_for_json(self, obj):
        """Recursively sanitize object for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, str):
            # Remove or replace problematic characters and limit length
            sanitized = obj.replace('\x00', '').replace('\b', '').replace('\f', '')
            sanitized = sanitized.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            # Limit string length to prevent huge JSON
            if len(sanitized) > 10000:
                sanitized = sanitized[:10000] + "... [truncated]"
            return sanitized
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif obj is None:
            return None
        elif isinstance(obj, (int, float, bool)):
            return obj
        else:
            # Convert unknown types to string
            return str(obj)
    
    def _create_html_report(self):
        """Create the HTML content for the API report"""
        # Ensure we have data
        if not self.api_calls:
            self.api_calls = []
        
        # Calculate statistics
        total_calls = len(self.api_calls)
        successful_calls = len([call for call in self.api_calls if 200 <= call.get('status', 0) < 300])
        error_calls = len([call for call in self.api_calls if call.get('status', 0) >= 400])
        
        # Group by status codes and methods
        status_counts = {}
        method_counts = {'GET': 0, 'POST': 0, 'PUT': 0, 'DELETE': 0, 'PATCH': 0, 'OPTIONS': 0, 'HEAD': 0}
        
        for call in self.api_calls:
            status = call.get('status', 0)
            status_counts[status] = status_counts.get(status, 0) + 1
            
            method = call.get('method', 'UNKNOWN').upper()
            if method in method_counts:
                method_counts[method] += 1
            else:
                method_counts[method] = 1
        
        # Sanitize and create JSON data for JavaScript
        try:
            sanitized_api_calls = self._sanitize_for_json(self.api_calls)
            api_calls_json = json.dumps(sanitized_api_calls, indent=2, cls=DateTimeEncoder, ensure_ascii=False)
            # Escape for safe HTML embedding
            api_calls_json = html.escape(api_calls_json)
        except Exception as e:
            logger.error(f"Error serializing API calls to JSON: {e}")
            api_calls_json = "[]"  # Fallback to empty array
        
        # Generate method options safely
        method_options = ""
        for method in sorted(method_counts.keys()):
            if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']:
                method_options += f'<option value="{html.escape(method)}">{html.escape(method)}</option>'
        
        # Generate status options safely
        status_options = ""
        for status in sorted(status_counts.keys()):
            status_options += f'<option value="{status}">{status}</option>'
        
        html_template = f"""<!DOCTYPE html>
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
        
        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            margin: 20px;
            border-radius: 5px;
            border: 1px solid #f5c6cb;
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
                <div class="stat-number warning">{len(self.api_calls) - successful_calls - error_calls}</div>
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
                    {method_options}
                </select>
            </div>
            
            <div class="filter-group">
                <label for="statusFilter">Status:</label>
                <select id="statusFilter">
                    <option value="">All Status</option>
                    {status_options}
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
        try {{
            // API calls data - parse the escaped JSON
            const apiCallsJson = `{api_calls_json}`;
            const apiCalls = JSON.parse(apiCallsJson);
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
                    const methodMatch = !methodValue || (call.method && call.method === methodValue);
                    const statusMatch = !statusValue || (call.status && call.status.toString() === statusValue);
                    const urlMatch = !urlValue || (call.url && call.url.toLowerCase().includes(urlValue));
                    
                    return methodMatch && statusMatch && urlMatch;
                }});
                
                renderTable();
            }}
            
            // Safely get value from object
            function safeGet(obj, key, defaultValue = '') {{
                return obj && obj[key] !== undefined ? obj[key] : defaultValue;
            }}
            
            // Render table
            function renderTable() {{
                tableBody.innerHTML = '';
                
                if (filteredCalls.length === 0) {{
                    const row = document.createElement('tr');
                    row.innerHTML = '<td colspan="7" style="text-align: center; padding: 20px;">No API calls match the current filters</td>';
                    tableBody.appendChild(row);
                    return;
                }}
                
                filteredCalls.forEach((call, index) => {{
                    const row = document.createElement('tr');
                    
                    const timestamp = call.timestamp ? new Date(call.timestamp).toLocaleString() : 'N/A';
                    const method = safeGet(call, 'method', 'UNKNOWN');
                    const methodClass = `method-${{method.toLowerCase()}}`;
                    const status = safeGet(call, 'status', 0);
                    const statusText = safeGet(call, 'statusText', '');
                    const statusClass = `status-${{Math.floor(status / 100)}}xx`;
                    const url = safeGet(call, 'url', '');
                    const mimeType = safeGet(call, 'mimeType', 'N/A');
                    const responseBody = safeGet(call, 'responseBody', '');
                    const responsePreview = responseBody ? 
                        responseBody.substring(0, 100) + (responseBody.length > 100 ? '...' : '') : 
                        'No content';
                    
                    row.innerHTML = `
                        <td>${{timestamp}}</td>
                        <td><span class="method-badge ${{methodClass}}">${{method}}</span></td>
                        <td class="url-cell">${{url}}</td>
                        <td><span class="status-badge ${{statusClass}}">${{status}} ${{statusText}}</span></td>
                        <td>${{mimeType}}</td>
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
                    <p><strong>Method:</strong> ${{safeGet(call, 'method', 'N/A')}}</p>
                    <p><strong>URL:</strong> ${{safeGet(call, 'url', 'N/A')}}</p>
                    <p><strong>Timestamp:</strong> ${{call.timestamp ? new Date(call.timestamp).toLocaleString() : 'N/A'}}</p>
                    <p><strong>Request ID:</strong> ${{safeGet(call, 'requestId', 'N/A')}}</p>
                    
                    ${{call.requestData ? `
                    <h3>Request Data</h3>
                    <div class="json-viewer">${{call.requestData}}</div>
                    ` : ''}}
                    
                    ${{call.requestHeaders && Object.keys(call.requestHeaders).length > 0 ? `
                    <h3>Request Headers</h3>
                    <div class="json-viewer">${{JSON.stringify(call.requestHeaders, null, 2)}}</div>
                    ` : ''}}
                    
                    <h3>Response Details</h3>
                    <p><strong>Status:</strong> ${{safeGet(call, 'status', 'N/A')}} ${{safeGet(call, 'statusText', '')}}</p>
                    <p><strong>Content Type:</strong> ${{safeGet(call, 'mimeType', 'N/A')}}</p>
                    
                    ${{call.headers && Object.keys(call.headers).length > 0 ? `
                    <h3>Response Headers</h3>
                    <div class="json-viewer">${{JSON.stringify(call.headers, null, 2)}}</div>
                    ` : ''}}
                    
                    <h3>Response Body</h3>
                    <div class="json-viewer">${{safeGet(call, 'responseBody', 'No content')}}</div>
                `;
                
                modalContent.innerHTML = details;
                modal.style.display = 'block';
            }}
            
            // Make showDetails globally available
            window.showDetails = showDetails;
            
            // Initial render
            renderTable();
            
        }} catch (error) {{
            console.error('Error initializing API report:', error);
            document.body.innerHTML = `
                <div class="error-message">
                    <h2>Error Loading Report</h2>
                    <p>There was an error loading the API report data. Please check the console for more details.</p>
                    <p>Error: ${{error.message}}</p>
                </div>
            `;
        }}
    </script>
</body>
</html>"""
        
        return html_template
