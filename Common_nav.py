from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Remove the deprecated DesiredCapabilities import
from EP import UiAutomationHelper
import sys
import os
import time
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create separate logger for API calls
api_logger = logging.getLogger('api_calls')
api_handler = logging.FileHandler('api_calls.log')
api_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
api_logger.addHandler(api_handler)
api_logger.setLevel(logging.INFO)

class APICallMonitor:
    def __init__(self, driver):
        self.driver = driver
        self.api_calls = []
    
    def start_monitoring(self):
        """Enable performance logging to capture network events"""
        # Enable performance logging
        self.driver.execute_cdp_cmd('Network.enable', {})
        logger.info("Network monitoring enabled")
    
    def get_network_logs(self):
        """Retrieve and parse network logs for API calls"""
        try:
            logs = self.driver.get_log('performance')
            
            # First pass: collect all request data
            requests_data = {}
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.requestWillBeSent':
                    request_id = message['message']['params']['requestId']
                    request_info = message['message']['params']['request']
                    requests_data[request_id] = {
                        'method': request_info['method'],
                        'url': request_info['url'],
                        'headers': request_info.get('headers', {}),
                        'postData': request_info.get('postData', '')
                    }
            
            # Second pass: process responses and match with requests
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    request_id = message['message']['params']['requestId']
                    
                    # Filter for API calls (typically JSON responses or specific endpoints)
                    if self.is_api_call(response):
                        # Get method from the corresponding request
                        method = requests_data.get(request_id, {}).get('method', 'GET')
                        request_url = requests_data.get(request_id, {}).get('url', response['url'])
                        
                        api_call_info = {
                            'timestamp': datetime.now().isoformat(),
                            'url': request_url,
                            'method': method.upper(),
                            'status': response['status'],
                            'statusText': response['statusText'],
                            'mimeType': response['mimeType'],
                            'headers': response.get('headers', {}),
                            'requestHeaders': requests_data.get(request_id, {}).get('headers', {}),
                            'requestData': requests_data.get(request_id, {}).get('postData', ''),
                            'requestId': request_id
                        }
                        
                        # Try to get response body
                        try:
                            response_body = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                            api_call_info['responseBody'] = response_body.get('body', '')
                        except Exception as e:
                            api_call_info['responseBody'] = f"Could not retrieve body: {str(e)}"
                        
                        self.api_calls.append(api_call_info)
                        self.log_api_call(api_call_info)
        
        except Exception as e:
            logger.error(f"Error retrieving network logs: {e}")
    
    def is_api_call(self, response):
        """Determine if the response is likely an API call"""
        url = response['url'].lower()
        mime_type = response.get('mimeType', '').lower()
        
        # Common patterns for API calls
        api_patterns = [
            'api/',
            '/api',
            'json',
            'ajax',
            'rest/',
            '/rest',
            'graphql',
            'xhr'
        ]
        
        # Check URL patterns
        url_is_api = any(pattern in url for pattern in api_patterns)
        
        # Check MIME type
        mime_is_api = 'json' in mime_type or 'xml' in mime_type
        
        # Exclude static resources
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.ttf']
        is_static = any(url.endswith(ext) for ext in static_extensions)
        
        return (url_is_api or mime_is_api) and not is_static
    
    def log_api_call(self, api_info):
        """Log API call information"""
        log_message = f"""
API Call Detected:
  URL: {api_info['url']}
  Method: {api_info['method']}
  Status: {api_info['status']} {api_info['statusText']}
  Content-Type: {api_info['mimeType']}
  Timestamp: {api_info['timestamp']}
  Response Body: {api_info['responseBody'][:200]}{'...' if len(str(api_info['responseBody'])) > 200 else ''}
  ---
"""
        api_logger.info(log_message)
        logger.info(f"API call logged: {api_info['method']} {api_info['url']} - Status: {api_info['status']}")
    
    def save_api_calls_to_file(self, filename='api_calls.json'):
        """Save all captured API calls to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.api_calls, f, indent=2)
            logger.info(f"API calls saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving API calls to file: {e}")
    
    def generate_html_report(self, filename='api_calls_report.html'):
        """Generate a comprehensive HTML report of all API calls"""
        try:
            html_content = self._create_html_report()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML report generated: {filename}")
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
    
    def _create_html_report(self):
        """Create the HTML content for the API report"""
        # Calculate statistics
        total_calls = len(self.api_calls)
        successful_calls = len([call for call in self.api_calls if 200 <= call['status'] < 300])
        error_calls = len([call for call in self.api_calls if call['status'] >= 400])
        
        # Group by status codes and methods
        status_counts = {}
        method_counts = {'GET': 0, 'POST': 0, 'PUT': 0, 'DELETE': 0, 'PATCH': 0, 'OPTIONS': 0, 'HEAD': 0}
        for call in self.api_calls:
            status_counts[call['status']] = status_counts.get(call['status'], 0) + 1
            method = call['method'].upper()
            if method in method_counts:
                method_counts[method] += 1
            else:
                method_counts[method] = 1
        
        # Create JSON data for JavaScript
        api_calls_json = json.dumps(self.api_calls, indent=2)
        
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
        
        return html_template
    
    def print_summary(self):
        """Print a summary of captured API calls"""
        print(f"\n=== API Calls Summary ===")
        print(f"Total API calls captured: {len(self.api_calls)}")
        
        if self.api_calls:
            print("\nAPI Endpoints:")
            for call in self.api_calls:
                print(f"  {call['method']} {call['url']} - {call['status']}")

# Add the directory containing EP.py to the system path
ep_dir = '/Users/pratik/Downloads/Assesment/Ui_Automation/'
if os.path.exists(os.path.join(ep_dir, 'EP.py')):
    sys.path.append(ep_dir)
else:
    logger.error(f"EP.py not found in {ep_dir}")
    exit(1)

driver_path = '/Users/pratik/Downloads/Assesment/Resource/chromedriver'

service = Service(executable_path=driver_path)

options = webdriver.ChromeOptions()
options.add_argument("--verbose")
options.add_experimental_option("detach", True)

# Enable performance logging for network monitoring (modern approach)
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

# Add arguments for bypassing face detection
options.add_argument("--use-fake-device-for-media-stream")
options.add_argument("--use-fake-ui-for-media-stream")
options.add_argument("--use-file-for-fake-video-capture=/Users/pratik/Downloads/Assesment/Ui_Automation/Resources/sample.y4m")
options.add_argument("--use-file-for-fake-audio-capture=/Users/pratik/Downloads/Assesment/Ui_Automation/Resources/sample_audio.wav")

try:
    logger.info("Initializing Chrome WebDriver with camera, microphone permissions, and network monitoring")
    prefs = {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.geolocation": 1,
        "profile.default_content_setting_values.notifications": 1
    }
    options.add_experimental_option("prefs", prefs)
    
    # Initialize driver with performance logging capabilities
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    
    # Initialize API monitor
    api_monitor = APICallMonitor(driver)
    api_monitor.start_monitoring()
    
    driver.get("https://www.vmock.com/")
    
    # Start periodic API monitoring
    api_monitor.get_network_logs()
    
except Exception as e:
    logger.error(f"Error launching ChromeDriver: {e}")
    exit(1)

# Create helper instance
logger.info("Creating UiAutomationHelper instance")
helper = UiAutomationHelper(driver)

# Accept cookies if the button is present
try:
    logger.info("Checking for cookie acceptance popup")
    if driver.find_elements(By.XPATH, "//div[@class='modal-content']"):
        driver.find_element(By.XPATH, "//button[@class='btn btn-primary accept']").click()
        logger.info("Accepted cookies")
        api_monitor.get_network_logs()  # Check for API calls after cookie acceptance
except Exception as e:
    logger.error(f"Cookie acceptance error: {e}")

# Navigate to login
try:
    logger.info("Attempting to navigate to login")
    if driver.find_elements(By.XPATH, "//div[@class='login-btn-container']"):
        driver.find_element(By.XPATH, "//a[@class='btn login-btn anim-btn btn-primary-web']").click()
        logger.info("Login button clicked")
        api_monitor.get_network_logs()  # Check for API calls after login navigation
except Exception as e:
    logger.error(f"Login navigation error: {e}")

# Login process
wait = WebDriverWait(driver, 10)
try:
    logger.info("Starting login process")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='button']"))).click()
    api_monitor.get_network_logs()  # Check for API calls
    
    email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
    email_field.send_keys("epitch-epitch_live21773@vmock.com")
    
    password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
    password_field.send_keys("1kI9vICw*9")
    
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    login_button.click()
    logger.info("Login successful")
    
    # Wait a moment for login API calls to complete
    time.sleep(3)
    api_monitor.get_network_logs()  # Check for login API calls
    
except Exception as e:
    logger.error(f"Login error: {e}")

# Dashboard navigation
try:
    logger.info("Navigating to dashboard")
    dashboard_nav = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='collapse navbar-collapse']")))
    interview_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='interview dropdown']")))
    interview_link.click()
    logger.info("Interview dropdown clicked")
    api_monitor.get_network_logs()  # Check for dashboard API calls
    
    # Start the interview
    logger.info("Attempting to start interview")
    helper.click_start_interview_button()
    api_monitor.get_network_logs()  # Check for interview start API calls

    # Close instructions popup with logging
    logger.info("Attempting to close instructions popup")
    helper.close_instructions_popup()
    api_monitor.get_network_logs()

    # Start calibration
    logger.info("Starting calibration")
    helper.start_calicration()
    logger.info("Calibration started successfully")
    time.sleep(5)
    api_monitor.get_network_logs()  # Check for calibration API calls
    
    logger.info("Calibration completed, proceeding with interview")
    time.sleep(10)
    api_monitor.get_network_logs()
    
    logger.info("Waiting for interview to be ready")
    time.sleep(10)
    api_monitor.get_network_logs()
    
    logger.info("Interview recording is ready, proceeding with the next steps")
    time.sleep(20)
    api_monitor.get_network_logs()
    
    # End interview
    logger.info("Ending interview")
    helper.end_interview()
    api_monitor.get_network_logs()  # Check for interview end API calls
    
    # Navigate to summary
    helper.navigate_to_summary_page()
    logger.info("Navigated to summary page successfully")
    api_monitor.get_network_logs()  # Check for summary page API calls
    
except Exception as e:
    logger.error(f"Dashboard navigation error: {e}")

# Final API monitoring and cleanup
logger.info("Final API call monitoring...")
time.sleep(2)
api_monitor.get_network_logs()

# Save API calls and generate HTML report
api_monitor.save_api_calls_to_file()
api_monitor.generate_html_report()
api_monitor.print_summary()

logger.info("Script execution completed")
time.sleep(5)
