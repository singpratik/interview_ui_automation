import json
from datetime import datetime
import logging
from typing import List, Dict, Any
from selenium import webdriver
from common import logger, api_logger

class APICallMonitor:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.api_calls: List[Dict[str, Any]] = []
    
    def start_monitoring(self) -> None:
        """Enable performance logging to capture network events"""
        self.driver.execute_cdp_cmd('Network.enable', {})
        logger.info("Network monitoring enabled")
    
    def get_network_logs(self) -> None:
        """Retrieve and parse network logs for API calls"""
        try:
            logs = self.driver.get_log('performance')
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
            
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    request_id = message['message']['params']['requestId']
                    
                    if self.is_api_call(response):
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
                        
                        try:
                            response_body = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                            api_call_info['responseBody'] = response_body.get('body', '')
                        except Exception as e:
                            api_call_info['responseBody'] = f"Could not retrieve body: {str(e)}"
                        
                        self.api_calls.append(api_call_info)
                        self.log_api_call(api_call_info)
        
        except Exception as e:
            logger.error(f"Error retrieving network logs: {e}")
    
    def is_api_call(self, response: Dict[str, Any]) -> bool:
        """Determine if the response is likely an API call"""
        url = response['url'].lower()
        mime_type = response.get('mimeType', '').lower()
        
        api_patterns = ['api/', '/api', 'json', 'ajax', 'rest/', '/rest', 'graphql', 'xhr']
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.ttf']
        
        url_is_api = any(pattern in url for pattern in api_patterns)
        mime_is_api = 'json' in mime_type or 'xml' in mime_type
        is_static = any(url.endswith(ext) for ext in static_extensions)
        
        return (url_is_api or mime_is_api) and not is_static
    
    def log_api_call(self, api_info: Dict[str, Any]) -> None:
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
    
    def save_api_calls_to_file(self, filename: str = 'api_calls.json') -> None:
        """Save all captured API calls to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.api_calls, f, indent=2)
            logger.info(f"API calls saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving API calls to file: {e}")
    
    def print_summary(self) -> None:
        """Print a summary of captured API calls"""
        print(f"\n=== API Calls Summary ===")
        print(f"Total API calls captured: {len(self.api_calls)}")
        
        if self.api_calls:
            print("\nAPI Endpoints:")
            for call in self.api_calls:
                print(f"  {call['method']} {call['url']} - {call['status']}")