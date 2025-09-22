"""
Web Automation Agent for Brebot.
An AI agent specialized in web automation, browser control, and web scraping.
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from bs4 import BeautifulSoup
import requests
from requests_html import HTMLSession

from config import get_llm_config, get_embedding_config, settings
from utils import brebot_logger


class WebAutomationAgent:
    """Web Automation Agent that can handle browser automation and web scraping."""
    
    def __init__(self, llm_config: dict = None, embedding_config: dict = None):
        """
        Initialize the Web Automation Agent.
        
        Args:
            llm_config: LLM configuration dictionary
            embedding_config: Embedding configuration dictionary
        """
        self.llm_config = llm_config or get_llm_config(settings)
        self.embedding_config = embedding_config or get_embedding_config(settings)
        
        # Browser instances
        self.playwright_browser: Optional[Browser] = None
        self.selenium_driver: Optional[webdriver.Chrome] = None
        self.current_page: Optional[Page] = None
        
        # Configuration
        self.headless = True
        self.browser_type = "chromium"  # chromium, firefox, webkit
        self.timeout = 30000  # 30 seconds
        
        brebot_logger.log_agent_action(
            agent_name="WebAutomationAgent",
            action="initialized",
            details={
                "browser_type": self.browser_type,
                "headless": self.headless,
                "timeout": self.timeout
            }
        )
    
    async def start_browser(self, browser_type: str = "chromium", headless: bool = True) -> bool:
        """
        Start a browser instance.
        
        Args:
            browser_type: Type of browser (chromium, firefox, webkit)
            headless: Whether to run in headless mode
            
        Returns:
            bool: True if browser started successfully
        """
        try:
            self.browser_type = browser_type
            self.headless = headless
            
            if not self.playwright_browser:
                playwright = await async_playwright().start()
                
                if browser_type == "chromium":
                    self.playwright_browser = await playwright.chromium.launch(
                        headless=headless,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                elif browser_type == "firefox":
                    self.playwright_browser = await playwright.firefox.launch(headless=headless)
                elif browser_type == "webkit":
                    self.playwright_browser = await playwright.webkit.launch(headless=headless)
                else:
                    raise ValueError(f"Unsupported browser type: {browser_type}")
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="browser_started",
                details={
                    "browser_type": browser_type,
                    "headless": headless
                }
            )
            
            return True
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="browser_start_failed",
                details={"error": str(e)}
            )
            return False
    
    async def start_selenium_browser(self, browser_type: str = "chrome", headless: bool = True) -> bool:
        """
        Start a Selenium browser instance.
        
        Args:
            browser_type: Type of browser (chrome, firefox)
            headless: Whether to run in headless mode
            
        Returns:
            bool: True if browser started successfully
        """
        try:
            if browser_type == "chrome":
                options = ChromeOptions()
                if headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                
                service = ChromeService(ChromeDriverManager().install())
                self.selenium_driver = webdriver.Chrome(service=service, options=options)
                
            elif browser_type == "firefox":
                options = FirefoxOptions()
                if headless:
                    options.add_argument("--headless")
                
                service = FirefoxService(GeckoDriverManager().install())
                self.selenium_driver = webdriver.Firefox(service=service, options=options)
            
            self.selenium_driver.set_page_load_timeout(30)
            self.selenium_driver.implicitly_wait(10)
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="selenium_browser_started",
                details={
                    "browser_type": browser_type,
                    "headless": headless
                }
            )
            
            return True
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="selenium_browser_start_failed",
                details={"error": str(e)}
            )
            return False
    
    async def navigate_to(self, url: str, wait_for_load: bool = True) -> bool:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_for_load: Whether to wait for page load
            
        Returns:
            bool: True if navigation successful
        """
        try:
            if self.playwright_browser:
                context = await self.playwright_browser.new_context()
                self.current_page = await context.new_page()
                await self.current_page.goto(url, wait_until="networkidle" if wait_for_load else "load")
                
            elif self.selenium_driver:
                self.selenium_driver.get(url)
                if wait_for_load:
                    WebDriverWait(self.selenium_driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="navigated",
                details={"url": url}
            )
            
            return True
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="navigation_failed",
                details={"url": url, "error": str(e)}
            )
            return False
    
    async def click_element(self, selector: str, selector_type: str = "css") -> bool:
        """
        Click an element on the page.
        
        Args:
            selector: Element selector
            selector_type: Type of selector (css, xpath, text)
            
        Returns:
            bool: True if click successful
        """
        try:
            if self.current_page:
                if selector_type == "css":
                    await self.current_page.click(selector)
                elif selector_type == "xpath":
                    await self.current_page.click(f"xpath={selector}")
                elif selector_type == "text":
                    await self.current_page.click(f"text={selector}")
                    
            elif self.selenium_driver:
                if selector_type == "css":
                    element = self.selenium_driver.find_element(By.CSS_SELECTOR, selector)
                elif selector_type == "xpath":
                    element = self.selenium_driver.find_element(By.XPATH, selector)
                elif selector_type == "text":
                    element = self.selenium_driver.find_element(By.LINK_TEXT, selector)
                
                element.click()
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="element_clicked",
                details={"selector": selector, "selector_type": selector_type}
            )
            
            return True
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="click_failed",
                details={"selector": selector, "error": str(e)}
            )
            return False
    
    async def fill_form(self, form_data: Dict[str, str]) -> bool:
        """
        Fill form fields with provided data.
        
        Args:
            form_data: Dictionary mapping field selectors to values
            
        Returns:
            bool: True if form filling successful
        """
        try:
            for selector, value in form_data.items():
                if self.current_page:
                    await self.current_page.fill(selector, value)
                elif self.selenium_driver:
                    element = self.selenium_driver.find_element(By.CSS_SELECTOR, selector)
                    element.clear()
                    element.send_keys(value)
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="form_filled",
                details={"fields_count": len(form_data)}
            )
            
            return True
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="form_fill_failed",
                details={"error": str(e)}
            )
            return False
    
    async def scrape_page(self, selectors: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Scrape data from the current page.
        
        Args:
            selectors: Dictionary mapping data names to CSS selectors
            
        Returns:
            Dict containing scraped data
        """
        try:
            scraped_data = {}
            
            if self.current_page:
                content = await self.current_page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                if selectors:
                    for name, selector in selectors.items():
                        elements = soup.select(selector)
                        scraped_data[name] = [elem.get_text(strip=True) for elem in elements]
                else:
                    # Default scraping - get all text content
                    scraped_data['page_title'] = soup.title.string if soup.title else ""
                    scraped_data['all_text'] = soup.get_text(strip=True)
                    
            elif self.selenium_driver:
                if selectors:
                    for name, selector in selectors.items():
                        elements = self.selenium_driver.find_elements(By.CSS_SELECTOR, selector)
                        scraped_data[name] = [elem.text for elem in elements]
                else:
                    scraped_data['page_title'] = self.selenium_driver.title
                    scraped_data['all_text'] = self.selenium_driver.find_element(By.TAG_NAME, "body").text
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="page_scraped",
                details={"data_points": len(scraped_data)}
            )
            
            return scraped_data
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="scraping_failed",
                details={"error": str(e)}
            )
            return {}
    
    async def take_screenshot(self, filename: str = None) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            filename: Optional filename for the screenshot
            
        Returns:
            str: Path to the screenshot file
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            screenshot_path = Path(settings.default_work_dir) / "screenshots" / filename
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.current_page:
                await self.current_page.screenshot(path=str(screenshot_path))
            elif self.selenium_driver:
                self.selenium_driver.save_screenshot(str(screenshot_path))
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="screenshot_taken",
                details={"filename": filename}
            )
            
            return str(screenshot_path)
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="screenshot_failed",
                details={"error": str(e)}
            )
            return ""
    
    async def wait_for_element(self, selector: str, timeout: int = 10) -> bool:
        """
        Wait for an element to appear on the page.
        
        Args:
            selector: Element selector
            timeout: Timeout in seconds
            
        Returns:
            bool: True if element found within timeout
        """
        try:
            if self.current_page:
                await self.current_page.wait_for_selector(selector, timeout=timeout * 1000)
            elif self.selenium_driver:
                WebDriverWait(self.selenium_driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            
            return True
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="wait_timeout",
                details={"selector": selector, "timeout": timeout, "error": str(e)}
            )
            return False
    
    async def execute_javascript(self, script: str) -> Any:
        """
        Execute JavaScript on the current page.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Result of JavaScript execution
        """
        try:
            if self.current_page:
                result = await self.current_page.evaluate(script)
            elif self.selenium_driver:
                result = self.selenium_driver.execute_script(script)
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="javascript_executed",
                details={"script_length": len(script)}
            )
            
            return result
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="javascript_failed",
                details={"error": str(e)}
            )
            return None
    
    async def close_browser(self):
        """Close the browser instance."""
        try:
            if self.playwright_browser:
                await self.playwright_browser.close()
                self.playwright_browser = None
                self.current_page = None
                
            if self.selenium_driver:
                self.selenium_driver.quit()
                self.selenium_driver = None
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="browser_closed"
            )
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="browser_close_failed",
                details={"error": str(e)}
            )
    
    async def automate_workflow(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a complete automation workflow.
        
        Args:
            workflow_steps: List of workflow steps with actions and parameters
            
        Returns:
            Dict containing workflow results
        """
        results = {
            "success": True,
            "steps_completed": 0,
            "total_steps": len(workflow_steps),
            "errors": [],
            "data": {}
        }
        
        try:
            for i, step in enumerate(workflow_steps):
                action = step.get("action")
                params = step.get("params", {})
                
                if action == "navigate":
                    success = await self.navigate_to(params.get("url"))
                elif action == "click":
                    success = await self.click_element(
                        params.get("selector"),
                        params.get("selector_type", "css")
                    )
                elif action == "fill_form":
                    success = await self.fill_form(params.get("form_data", {}))
                elif action == "scrape":
                    data = await self.scrape_page(params.get("selectors"))
                    results["data"][f"step_{i}"] = data
                    success = True
                elif action == "wait":
                    success = await self.wait_for_element(
                        params.get("selector"),
                        params.get("timeout", 10)
                    )
                elif action == "screenshot":
                    filename = await self.take_screenshot(params.get("filename"))
                    results["data"][f"step_{i}"] = {"screenshot": filename}
                    success = bool(filename)
                elif action == "javascript":
                    result = await self.execute_javascript(params.get("script"))
                    results["data"][f"step_{i}"] = {"javascript_result": result}
                    success = result is not None
                else:
                    results["errors"].append(f"Unknown action: {action}")
                    success = False
                
                if success:
                    results["steps_completed"] += 1
                else:
                    results["errors"].append(f"Step {i+1} failed: {action}")
                    if not params.get("continue_on_error", False):
                        results["success"] = False
                        break
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="workflow_completed",
                details={
                    "steps_completed": results["steps_completed"],
                    "total_steps": results["total_steps"],
                    "success": results["success"]
                }
            )
            
        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Workflow error: {str(e)}")
            
            brebot_logger.log_agent_action(
                agent_name="WebAutomationAgent",
                action="workflow_failed",
                details={"error": str(e)}
            )
        
        return results
