"""
Web Automation Tools for CrewAI.
Tools for browser automation, web scraping, and n8n integration.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from agents.web_automation_agent import WebAutomationAgent
from integrations.n8n_client import N8NClient
from utils import brebot_logger


class WebAutomationInput(BaseModel):
    """Input schema for web automation tools."""
    url: str = Field(description="URL to navigate to")
    headless: bool = Field(default=True, description="Whether to run browser in headless mode")
    browser_type: str = Field(default="chromium", description="Browser type (chromium, firefox, webkit)")


class WebScrapingInput(BaseModel):
    """Input schema for web scraping tools."""
    url: str = Field(description="URL to scrape")
    selectors: Dict[str, str] = Field(default={}, description="CSS selectors for specific data extraction")
    wait_for_element: Optional[str] = Field(default=None, description="CSS selector to wait for before scraping")


class FormFillingInput(BaseModel):
    """Input schema for form filling tools."""
    url: str = Field(description="URL containing the form")
    form_data: Dict[str, str] = Field(description="Form field selectors mapped to values")
    submit_button_selector: Optional[str] = Field(default=None, description="CSS selector for submit button")


class ScreenshotInput(BaseModel):
    """Input schema for screenshot tools."""
    url: str = Field(description="URL to take screenshot of")
    filename: Optional[str] = Field(default=None, description="Filename for the screenshot")
    full_page: bool = Field(default=False, description="Whether to capture full page")


class N8NWorkflowInput(BaseModel):
    """Input schema for n8n workflow tools."""
    workflow_id: str = Field(description="ID of the n8n workflow")
    input_data: Dict[str, Any] = Field(default={}, description="Input data for the workflow")
    n8n_url: str = Field(default="http://localhost:5678", description="N8N instance URL")


class WebAutomationTool(BaseTool):
    """Tool for general web automation tasks."""
    
    name: str = "web_automation"
    description: str = "Perform web automation tasks including navigation, clicking, and form interactions"
    args_schema: type[BaseModel] = WebAutomationInput
    
    def _run(self, url: str, headless: bool = True, browser_type: str = "chromium", 
             actions: List[Dict[str, Any]] = None) -> str:
        """
        Run web automation tasks.
        
        Args:
            url: URL to navigate to
            headless: Whether to run in headless mode
            browser_type: Type of browser to use
            actions: List of actions to perform
            
        Returns:
            Result of the automation task
        """
        async def _async_run():
            agent = WebAutomationAgent()
            
            try:
                # Start browser
                success = await agent.start_browser(browser_type, headless)
                if not success:
                    return "Failed to start browser"
                
                # Navigate to URL
                success = await agent.navigate_to(url)
                if not success:
                    return f"Failed to navigate to {url}"
                
                # Perform actions if provided
                if actions:
                    for action in actions:
                        action_type = action.get("type")
                        params = action.get("params", {})
                        
                        if action_type == "click":
                            await agent.click_element(
                                params.get("selector"),
                                params.get("selector_type", "css")
                            )
                        elif action_type == "fill_form":
                            await agent.fill_form(params.get("form_data", {}))
                        elif action_type == "wait":
                            await agent.wait_for_element(
                                params.get("selector"),
                                params.get("timeout", 10)
                            )
                        elif action_type == "javascript":
                            await agent.execute_javascript(params.get("script"))
                
                # Take screenshot for verification
                screenshot_path = await agent.take_screenshot()
                
                await agent.close_browser()
                
                return f"Web automation completed successfully. Screenshot saved to: {screenshot_path}"
                
            except Exception as e:
                await agent.close_browser()
                return f"Web automation failed: {str(e)}"
        
        return asyncio.run(_async_run())


class WebScrapingTool(BaseTool):
    """Tool for web scraping tasks."""
    
    name: str = "web_scraping"
    description: str = "Scrape data from web pages using CSS selectors"
    args_schema: type[BaseModel] = WebScrapingInput
    
    def _run(self, url: str, selectors: Dict[str, str] = None, 
             wait_for_element: str = None) -> str:
        """
        Scrape data from a web page.
        
        Args:
            url: URL to scrape
            selectors: CSS selectors for specific data extraction
            wait_for_element: Element to wait for before scraping
            
        Returns:
            Scraped data as JSON string
        """
        async def _async_run():
            agent = WebAutomationAgent()
            
            try:
                # Start browser
                success = await agent.start_browser("chromium", True)
                if not success:
                    return "Failed to start browser"
                
                # Navigate to URL
                success = await agent.navigate_to(url)
                if not success:
                    return f"Failed to navigate to {url}"
                
                # Wait for specific element if specified
                if wait_for_element:
                    await agent.wait_for_element(wait_for_element)
                
                # Scrape data
                scraped_data = await agent.scrape_page(selectors)
                
                await agent.close_browser()
                
                return json.dumps(scraped_data, indent=2)
                
            except Exception as e:
                await agent.close_browser()
                return f"Web scraping failed: {str(e)}"
        
        return asyncio.run(_async_run())


class FormFillingTool(BaseTool):
    """Tool for filling web forms."""
    
    name: str = "form_filling"
    description: str = "Fill web forms automatically"
    args_schema: type[BaseModel] = FormFillingInput
    
    def _run(self, url: str, form_data: Dict[str, str], 
             submit_button_selector: str = None) -> str:
        """
        Fill a web form.
        
        Args:
            url: URL containing the form
            form_data: Form field selectors mapped to values
            submit_button_selector: CSS selector for submit button
            
        Returns:
            Result of form filling
        """
        async def _async_run():
            agent = WebAutomationAgent()
            
            try:
                # Start browser
                success = await agent.start_browser("chromium", True)
                if not success:
                    return "Failed to start browser"
                
                # Navigate to URL
                success = await agent.navigate_to(url)
                if not success:
                    return f"Failed to navigate to {url}"
                
                # Fill form
                success = await agent.fill_form(form_data)
                if not success:
                    return "Failed to fill form"
                
                # Submit form if button selector provided
                if submit_button_selector:
                    success = await agent.click_element(submit_button_selector)
                    if not success:
                        return "Failed to submit form"
                
                # Take screenshot
                screenshot_path = await agent.take_screenshot()
                
                await agent.close_browser()
                
                return f"Form filled successfully. Screenshot saved to: {screenshot_path}"
                
            except Exception as e:
                await agent.close_browser()
                return f"Form filling failed: {str(e)}"
        
        return asyncio.run(_async_run())


class ScreenshotTool(BaseTool):
    """Tool for taking web page screenshots."""
    
    name: str = "web_screenshot"
    description: str = "Take screenshots of web pages"
    args_schema: type[BaseModel] = ScreenshotInput
    
    def _run(self, url: str, filename: str = None, full_page: bool = False) -> str:
        """
        Take a screenshot of a web page.
        
        Args:
            url: URL to screenshot
            filename: Filename for the screenshot
            full_page: Whether to capture full page
            
        Returns:
            Path to the screenshot file
        """
        async def _async_run():
            agent = WebAutomationAgent()
            
            try:
                # Start browser
                success = await agent.start_browser("chromium", True)
                if not success:
                    return "Failed to start browser"
                
                # Navigate to URL
                success = await agent.navigate_to(url)
                if not success:
                    return f"Failed to navigate to {url}"
                
                # Take screenshot
                screenshot_path = await agent.take_screenshot(filename)
                
                await agent.close_browser()
                
                return f"Screenshot saved to: {screenshot_path}"
                
            except Exception as e:
                await agent.close_browser()
                return f"Screenshot failed: {str(e)}"
        
        return asyncio.run(_async_run())


class N8NWorkflowTool(BaseTool):
    """Tool for executing n8n workflows."""
    
    name: str = "n8n_workflow"
    description: str = "Execute n8n workflows and manage automation"
    args_schema: type[BaseModel] = N8NWorkflowInput
    
    def _run(self, workflow_id: str, input_data: Dict[str, Any] = None, 
             n8n_url: str = "http://localhost:5678") -> str:
        """
        Execute an n8n workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
            n8n_url: N8N instance URL
            
        Returns:
            Result of workflow execution
        """
        try:
            client = N8NClient(n8n_url)
            
            # Test connection
            if not client.test_connection():
                return f"Failed to connect to n8n at {n8n_url}"
            
            # Execute workflow
            result = client.execute_workflow(workflow_id, input_data)
            
            if "error" in result:
                return f"Workflow execution failed: {result['error']}"
            
            return f"Workflow {workflow_id} executed successfully. Result: {json.dumps(result, indent=2)}"
            
        except Exception as e:
            return f"N8N workflow execution failed: {str(e)}"


class N8NWorkflowManagerTool(BaseTool):
    """Tool for managing n8n workflows."""
    
    name: str = "n8n_workflow_manager"
    description: str = "Manage n8n workflows (create, update, activate, deactivate)"
    args_schema: type[BaseModel] = N8NWorkflowInput
    
    def _run(self, action: str, workflow_id: str = None, workflow_data: Dict[str, Any] = None,
             n8n_url: str = "http://localhost:5678") -> str:
        """
        Manage n8n workflows.
        
        Args:
            action: Action to perform (list, get, create, update, activate, deactivate, delete)
            workflow_id: ID of the workflow (required for most actions)
            workflow_data: Workflow data (required for create/update)
            n8n_url: N8N instance URL
            
        Returns:
            Result of the management action
        """
        try:
            client = N8NClient(n8n_url)
            
            # Test connection
            if not client.test_connection():
                return f"Failed to connect to n8n at {n8n_url}"
            
            if action == "list":
                workflows = client.get_workflows()
                return f"Found {len(workflows)} workflows: {json.dumps(workflows, indent=2)}"
            
            elif action == "get":
                if not workflow_id:
                    return "Workflow ID is required for get action"
                workflow = client.get_workflow(workflow_id)
                return json.dumps(workflow, indent=2)
            
            elif action == "create":
                if not workflow_data:
                    return "Workflow data is required for create action"
                result = client.create_workflow(workflow_data)
                return f"Workflow created: {json.dumps(result, indent=2)}"
            
            elif action == "update":
                if not workflow_id or not workflow_data:
                    return "Workflow ID and data are required for update action"
                result = client.update_workflow(workflow_id, workflow_data)
                return f"Workflow updated: {json.dumps(result, indent=2)}"
            
            elif action == "activate":
                if not workflow_id:
                    return "Workflow ID is required for activate action"
                success = client.activate_workflow(workflow_id)
                return f"Workflow {'activated' if success else 'activation failed'}"
            
            elif action == "deactivate":
                if not workflow_id:
                    return "Workflow ID is required for deactivate action"
                success = client.deactivate_workflow(workflow_id)
                return f"Workflow {'deactivated' if success else 'deactivation failed'}"
            
            elif action == "delete":
                if not workflow_id:
                    return "Workflow ID is required for delete action"
                success = client.delete_workflow(workflow_id)
                return f"Workflow {'deleted' if success else 'deletion failed'}"
            
            else:
                return f"Unknown action: {action}. Available actions: list, get, create, update, activate, deactivate, delete"
            
        except Exception as e:
            return f"N8N workflow management failed: {str(e)}"


class WebWorkflowTool(BaseTool):
    """Tool for creating complex web automation workflows."""
    
    name: str = "web_workflow"
    description: str = "Create and execute complex web automation workflows"
    args_schema: type[BaseModel] = WebAutomationInput
    
    def _run(self, workflow_steps: List[Dict[str, Any]], headless: bool = True, 
             browser_type: str = "chromium") -> str:
        """
        Execute a complex web automation workflow.
        
        Args:
            workflow_steps: List of workflow steps with actions and parameters
            headless: Whether to run in headless mode
            browser_type: Type of browser to use
            
        Returns:
            Result of the workflow execution
        """
        async def _async_run():
            agent = WebAutomationAgent()
            
            try:
                # Start browser
                success = await agent.start_browser(browser_type, headless)
                if not success:
                    return "Failed to start browser"
                
                # Execute workflow
                result = await agent.automate_workflow(workflow_steps)
                
                await agent.close_browser()
                
                return json.dumps(result, indent=2)
                
            except Exception as e:
                await agent.close_browser()
                return f"Web workflow execution failed: {str(e)}"
        
        return asyncio.run(_async_run())
