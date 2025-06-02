import random
import time
import asyncio
import aiohttp
import requests
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class APIProtectionManager:
    """
    Advanced API protection system with IP rotation, rate limiting, and ban prevention
    """
    
    def __init__(self):
        self.proxy_list = []
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Android 14; Mobile; rv:122.0) Gecko/122.0 Firefox/122.0"
        ]
        
        # Rate limiting tracking
        self.api_calls = {}  # api_key -> [timestamp, timestamp, ...]
        self.api_limits = {
            'gemini': {'calls_per_minute': 55, 'calls_per_hour': 1000, 'delay_between_calls': 1.2},
            'deepinfra': {'calls_per_minute': 50, 'calls_per_hour': 800, 'delay_between_calls': 1.5},
            'huggingface': {'calls_per_minute': 45, 'calls_per_hour': 600, 'delay_between_calls': 1.8},
            'openai': {'calls_per_minute': 40, 'calls_per_hour': 500, 'delay_between_calls': 2.0}
        }
        
        # Proxy rotation settings
        self.current_proxy_index = 0
        self.proxy_rotation_enabled = False
        
        # Load free proxy services (optional)
        self.free_proxy_apis = [
            "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        ]
        
        # Request delays and backoff
        self.base_delay = 1.0
        self.max_retries = 3
        self.backoff_multiplier = 2.0
        
    async def initialize_proxy_rotation(self, enable_rotation: bool = True):
        """Initialize proxy rotation system"""
        self.proxy_rotation_enabled = enable_rotation
        
        if enable_rotation:
            await self._load_proxy_list()
            logger.info(f"Loaded {len(self.proxy_list)} proxies for rotation")
    
    async def _load_proxy_list(self):
        """Load proxy list from various sources"""
        # You can add your premium proxy service here
        # For now, we'll use a basic list
        
        # Example premium proxy services (you'd need to subscribe):
        premium_proxies = [
            # Add your premium proxy endpoints here
            # {"http": "http://username:password@proxy1.example.com:8080"},
            # {"http": "http://username:password@proxy2.example.com:8080"},
        ]
        
        self.proxy_list = premium_proxies
        
        # Optionally load free proxies (less reliable)
        if len(self.proxy_list) == 0:
            logger.warning("No premium proxies configured. Consider adding premium proxy services for better reliability.")
    
    def get_random_headers(self) -> Dict[str, str]:
        """Generate random headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': random.choice(['en-US,en;q=0.9', 'en-GB,en;q=0.9', 'en-US,en;q=0.8']),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    def get_current_proxy(self) -> Optional[Dict]:
        """Get current proxy for rotation"""
        if not self.proxy_rotation_enabled or len(self.proxy_list) == 0:
            return None
        
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy
    
    async def check_rate_limit(self, api_type: str, api_key: str) -> bool:
        """Check if we can make an API call without hitting rate limits"""
        now = datetime.now()
        key_identifier = f"{api_type}_{api_key[:8]}"  # Use first 8 chars for privacy
        
        if key_identifier not in self.api_calls:
            self.api_calls[key_identifier] = []
        
        calls = self.api_calls[key_identifier]
        
        # Remove calls older than 1 hour
        calls[:] = [call_time for call_time in calls if now - call_time < timedelta(hours=1)]
        
        # Remove calls older than 1 minute for minute-based limiting
        recent_calls = [call_time for call_time in calls if now - call_time < timedelta(minutes=1)]
        
        limits = self.api_limits.get(api_type, {})
        calls_per_minute = limits.get('calls_per_minute', 50)
        calls_per_hour = limits.get('calls_per_hour', 1000)
        
        # Check limits
        if len(recent_calls) >= calls_per_minute:
            logger.warning(f"Rate limit reached for {api_type} (minute limit)")
            return False
        
        if len(calls) >= calls_per_hour:
            logger.warning(f"Rate limit reached for {api_type} (hour limit)")
            return False
        
        return True
    
    async def add_api_call(self, api_type: str, api_key: str):
        """Record an API call for rate limiting"""
        key_identifier = f"{api_type}_{api_key[:8]}"
        if key_identifier not in self.api_calls:
            self.api_calls[key_identifier] = []
        
        self.api_calls[key_identifier].append(datetime.now())
    
    async def get_recommended_delay(self, api_type: str) -> float:
        """Get recommended delay between calls for this API"""
        limits = self.api_limits.get(api_type, {})
        base_delay = limits.get('delay_between_calls', 1.0)
        
        # Add some randomization to avoid predictable patterns
        jitter = random.uniform(0.1, 0.5)
        return base_delay + jitter
    
    async def make_protected_request(self, 
                                   method: str,
                                   url: str, 
                                   api_type: str,
                                   api_key: str,
                                   **kwargs) -> Optional[Dict]:
        """
        Make a protected API request with IP rotation and rate limiting
        """
        
        # Check rate limits
        if not await self.check_rate_limit(api_type, api_key):
            logger.warning(f"Rate limit hit for {api_type}, waiting...")
            await asyncio.sleep(60)  # Wait 1 minute if rate limited
            return None
        
        # Get recommended delay
        delay = await self.get_recommended_delay(api_type)
        await asyncio.sleep(delay)
        
        # Prepare headers
        headers = self.get_random_headers()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        # Get proxy
        proxy = self.get_current_proxy()
        if proxy:
            kwargs['proxy'] = proxy['http']
        
        # Add timeout
        kwargs['timeout'] = kwargs.get('timeout', 30)
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, **kwargs) as response:
                        if response.status == 200:
                            await self.add_api_call(api_type, api_key)
                            result = await response.json()
                            logger.info(f"Successful {api_type} API call (attempt {attempt + 1})")
                            return result
                        elif response.status == 429:  # Rate limited
                            logger.warning(f"Rate limited by {api_type} API, waiting...")
                            await asyncio.sleep(60 * (attempt + 1))
                        elif response.status == 403:  # Forbidden/banned
                            logger.error(f"IP potentially banned by {api_type}, rotating...")
                            if proxy:
                                # Remove bad proxy
                                if proxy in self.proxy_list:
                                    self.proxy_list.remove(proxy)
                            await asyncio.sleep(30)
                        else:
                            logger.warning(f"API call failed with status {response.status}")
                            
            except Exception as e:
                logger.error(f"Request attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (self.backoff_multiplier ** attempt)
                    await asyncio.sleep(wait_time)
        
        logger.error(f"All {self.max_retries} attempts failed for {api_type} API")
        return None
    
    def add_premium_proxies(self, proxy_list: List[str]):
        """Add premium proxy list"""
        for proxy in proxy_list:
            self.proxy_list.append({"http": proxy})
        logger.info(f"Added {len(proxy_list)} premium proxies")
    
    def get_protection_stats(self) -> Dict:
        """Get current protection statistics"""
        return {
            "proxies_available": len(self.proxy_list),
            "proxy_rotation_enabled": self.proxy_rotation_enabled,
            "tracked_apis": len(self.api_calls),
            "current_proxy_index": self.current_proxy_index
        }

# Global protection manager instance
protection_manager = APIProtectionManager()

# Convenience functions for easy use
async def make_protected_api_call(method: str, url: str, api_type: str, api_key: str, **kwargs):
    """Convenience function for making protected API calls"""
    return await protection_manager.make_protected_request(method, url, api_type, api_key, **kwargs)

async def initialize_protection(enable_proxy_rotation: bool = True, premium_proxies: List[str] = None):
    """Initialize the protection system"""
    await protection_manager.initialize_proxy_rotation(enable_proxy_rotation)
    
    if premium_proxies:
        protection_manager.add_premium_proxies(premium_proxies)
    
    logger.info("API protection system initialized successfully")