"""
N8N Integration Client for Brebot.
Provides integration with n8n workflow automation platform.
"""

import asyncio
import json
import requests
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import base64

from utils import brebot_logger


class N8NClient:
    """Client for interacting with n8n workflow automation platform."""
    
    def __init__(self, base_url: str = "http://localhost:5678", api_key: str = None):
        """
        Initialize the N8N client.
        
        Args:
            base_url: Base URL of the n8n instance
            api_key: API key for authentication (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
        
        brebot_logger.log_agent_action(
            agent_name="N8NClient",
            action="initialized",
            details={"base_url": self.base_url, "has_api_key": bool(self.api_key)}
        )
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """
        Make a request to the n8n API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            
        Returns:
            Dict containing response data
        """
        url = f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="api_request_failed",
                details={"method": method, "endpoint": endpoint, "error": str(e)}
            )
            return {"error": str(e)}
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """
        Get all workflows from n8n.
        
        Returns:
            List of workflow dictionaries
        """
        result = self._make_request("GET", "workflows")
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="workflows_retrieved",
                details={"count": len(result.get("data", []))}
            )
        
        return result.get("data", [])
    
    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get a specific workflow by ID.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow dictionary
        """
        result = self._make_request("GET", f"workflows/{workflow_id}")
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="workflow_retrieved",
                details={"workflow_id": workflow_id}
            )
        
        return result
    
    def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new workflow.
        
        Args:
            workflow_data: Workflow configuration data
            
        Returns:
            Created workflow dictionary
        """
        result = self._make_request("POST", "workflows", data=workflow_data)
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="workflow_created",
                details={"workflow_id": result.get("id")}
            )
        
        return result
    
    def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing workflow.
        
        Args:
            workflow_id: ID of the workflow to update
            workflow_data: Updated workflow data
            
        Returns:
            Updated workflow dictionary
        """
        result = self._make_request("PUT", f"workflows/{workflow_id}", data=workflow_data)
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="workflow_updated",
                details={"workflow_id": workflow_id}
            )
        
        return result
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: ID of the workflow to delete
            
        Returns:
            True if deletion successful
        """
        result = self._make_request("DELETE", f"workflows/{workflow_id}")
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="workflow_deleted",
                details={"workflow_id": workflow_id}
            )
            return True
        
        return False
    
    def activate_workflow(self, workflow_id: str) -> bool:
        """
        Activate a workflow.
        
        Args:
            workflow_id: ID of the workflow to activate
            
        Returns:
            True if activation successful
        """
        result = self._make_request("POST", f"workflows/{workflow_id}/activate")
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="workflow_activated",
                details={"workflow_id": workflow_id}
            )
            return True
        
        return False
    
    def deactivate_workflow(self, workflow_id: str) -> bool:
        """
        Deactivate a workflow.
        
        Args:
            workflow_id: ID of the workflow to deactivate
            
        Returns:
            True if deactivation successful
        """
        result = self._make_request("POST", f"workflows/{workflow_id}/deactivate")
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="workflow_deactivated",
                details={"workflow_id": workflow_id}
            )
            return True
        
        return False
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a workflow manually.
        
        Args:
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
            
        Returns:
            Execution result
        """
        data = {"input": input_data} if input_data else {}
        result = self._make_request("POST", f"workflows/{workflow_id}/execute", data=data)
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="workflow_executed",
                details={"workflow_id": workflow_id}
            )
        
        return result
    
    def get_executions(self, workflow_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get workflow executions.
        
        Args:
            workflow_id: Optional workflow ID to filter executions
            limit: Maximum number of executions to return
            
        Returns:
            List of execution dictionaries
        """
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        
        result = self._make_request("GET", "executions", params=params)
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="executions_retrieved",
                details={"count": len(result.get("data", []))}
            )
        
        return result.get("data", [])
    
    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Get a specific execution by ID.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Execution dictionary
        """
        result = self._make_request("GET", f"executions/{execution_id}")
        
        if "error" not in result:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="execution_retrieved",
                details={"execution_id": execution_id}
            )
        
        return result
    
    def create_webhook_workflow(self, name: str, webhook_path: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a webhook-triggered workflow.
        
        Args:
            name: Name of the workflow
            webhook_path: Webhook path for triggering
            nodes: List of workflow nodes
            
        Returns:
            Created workflow dictionary
        """
        workflow_data = {
            "name": name,
            "active": True,
            "nodes": [
                {
                    "parameters": {
                        "path": webhook_path,
                        "httpMethod": "POST"
                    },
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [240, 300]
                }
            ] + nodes,
            "connections": {
                "Webhook": {
                    "main": [[{"node": nodes[0]["name"], "type": "main", "index": 0}]]
                }
            }
        }
        
        return self.create_workflow(workflow_data)
    
    def create_scheduled_workflow(self, name: str, cron_expression: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a scheduled workflow.
        
        Args:
            name: Name of the workflow
            cron_expression: Cron expression for scheduling
            nodes: List of workflow nodes
            
        Returns:
            Created workflow dictionary
        """
        workflow_data = {
            "name": name,
            "active": True,
            "nodes": [
                {
                    "parameters": {
                        "rule": {
                            "interval": [{"field": "cronExpression", "expression": cron_expression}]
                        }
                    },
                    "name": "Schedule Trigger",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "typeVersion": 1,
                    "position": [240, 300]
                }
            ] + nodes,
            "connections": {
                "Schedule Trigger": {
                    "main": [[{"node": nodes[0]["name"], "type": "main", "index": 0}]]
                }
            }
        }
        
        return self.create_workflow(workflow_data)
    
    def create_http_request_node(self, name: str, url: str, method: str = "GET", 
                                headers: Dict[str, str] = None, body: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create an HTTP Request node.
        
        Args:
            name: Name of the node
            url: URL to request
            method: HTTP method
            headers: Request headers
            body: Request body
            
        Returns:
            Node configuration dictionary
        """
        node = {
            "parameters": {
                "url": url,
                "method": method,
                "options": {}
            },
            "name": name,
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [460, 300]
        }
        
        if headers:
            node["parameters"]["options"]["headers"] = headers
        
        if body:
            node["parameters"]["options"]["body"] = body
        
        return node
    
    def create_code_node(self, name: str, code: str, language: str = "javascript") -> Dict[str, Any]:
        """
        Create a Code node.
        
        Args:
            name: Name of the node
            code: Code to execute
            language: Programming language
            
        Returns:
            Node configuration dictionary
        """
        return {
            "parameters": {
                "jsCode": code if language == "javascript" else "",
                "pythonCode": code if language == "python" else ""
            },
            "name": name,
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [680, 300]
        }
    
    def create_email_node(self, name: str, to_email: str, subject: str, 
                         message: str, from_email: str = None) -> Dict[str, Any]:
        """
        Create an Email node.
        
        Args:
            name: Name of the node
            to_email: Recipient email
            subject: Email subject
            message: Email message
            from_email: Sender email
            
        Returns:
            Node configuration dictionary
        """
        return {
            "parameters": {
                "fromEmail": from_email,
                "toEmail": to_email,
                "subject": subject,
                "message": message
            },
            "name": name,
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 2,
            "position": [900, 300]
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the status of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Status information
        """
        workflow = self.get_workflow(workflow_id)
        
        if "error" in workflow:
            return workflow
        
        return {
            "id": workflow.get("id"),
            "name": workflow.get("name"),
            "active": workflow.get("active", False),
            "created_at": workflow.get("createdAt"),
            "updated_at": workflow.get("updatedAt"),
            "nodes_count": len(workflow.get("nodes", [])),
            "connections_count": len(workflow.get("connections", {}))
        }
    
    def test_connection(self) -> bool:
        """
        Test the connection to n8n.
        
        Returns:
            True if connection successful
        """
        try:
            result = self._make_request("GET", "workflows")
            success = "error" not in result
            
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="connection_tested",
                details={"success": success}
            )
            
            return success
            
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="N8NClient",
                action="connection_test_failed",
                details={"error": str(e)}
            )
            return False
