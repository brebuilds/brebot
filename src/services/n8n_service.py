"""
n8n Integration Service for BreBot
Provides tools for managing n8n workflows via MCP
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx
from pydantic import BaseModel

from utils.logger import brebot_logger


class N8nWorkflow(BaseModel):
    """n8n workflow model."""
    id: str
    name: str
    active: bool
    tags: List[str] = []
    createdAt: str
    updatedAt: str
    nodes: int = 0


class N8nExecution(BaseModel):
    """n8n execution model."""
    id: str
    workflowId: str
    mode: str
    status: str
    startedAt: Optional[str] = None
    finishedAt: Optional[str] = None
    executionTime: Optional[int] = None


class N8nService:
    """Service for managing n8n workflows and executions."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize n8n service.
        
        Args:
            base_url: n8n instance URL (e.g., 'https://your-n8n.hostinger.com')
            api_key: n8n API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers['X-N8N-API-KEY'] = api_key
        
        brebot_logger.log_agent_action(
            agent_name="N8nService",
            action="initialized",
            details={
                "base_url": base_url,
                "has_api_key": bool(api_key)
            }
        )
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to n8n API."""
        url = f"{self.base_url}/api/v1{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=30.0,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                brebot_logger.log_error(
                    e, 
                    context=f"N8nService._make_request",
                    details={"method": method, "endpoint": endpoint, "status": getattr(e.response, 'status_code', None)}
                )
                raise Exception(f"n8n API error: {e}")
    
    async def list_workflows(self, active_only: bool = False) -> List[N8nWorkflow]:
        """List all workflows."""
        try:
            params = {}
            if active_only:
                params['filter'] = '{"active": true}'
            
            data = await self._make_request('GET', '/workflows', params=params)
            workflows = []
            
            for workflow_data in data.get('data', []):
                workflows.append(N8nWorkflow(
                    id=str(workflow_data['id']),
                    name=workflow_data['name'],
                    active=workflow_data.get('active', False),
                    tags=workflow_data.get('tags', []),
                    createdAt=workflow_data.get('createdAt', ''),
                    updatedAt=workflow_data.get('updatedAt', ''),
                    nodes=len(workflow_data.get('nodes', []))
                ))
            
            brebot_logger.log_agent_action(
                agent_name="N8nService",
                action="workflows_listed",
                details={"count": len(workflows), "active_only": active_only}
            )
            
            return workflows
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.list_workflows")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[N8nWorkflow]:
        """Get specific workflow by ID."""
        try:
            data = await self._make_request('GET', f'/workflows/{workflow_id}')
            
            if data:
                return N8nWorkflow(
                    id=str(data['id']),
                    name=data['name'],
                    active=data.get('active', False),
                    tags=data.get('tags', []),
                    createdAt=data.get('createdAt', ''),
                    updatedAt=data.get('updatedAt', ''),
                    nodes=len(data.get('nodes', []))
                )
            
            return None
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.get_workflow")
            raise
    
    async def execute_workflow(self, workflow_id: str, data: Optional[Dict] = None) -> str:
        """Execute a workflow and return execution ID."""
        try:
            payload = {}
            if data:
                payload['data'] = data
            
            response = await self._make_request(
                'POST', 
                f'/workflows/{workflow_id}/execute',
                json=payload
            )
            
            execution_id = response.get('executionId')
            
            brebot_logger.log_agent_action(
                agent_name="N8nService",
                action="workflow_executed",
                details={
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "has_data": bool(data)
                }
            )
            
            return execution_id
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.execute_workflow")
            raise
    
    async def get_execution_status(self, execution_id: str) -> Optional[N8nExecution]:
        """Get execution status by ID."""
        try:
            data = await self._make_request('GET', f'/executions/{execution_id}')
            
            if data:
                return N8nExecution(
                    id=str(data['id']),
                    workflowId=str(data.get('workflowId', '')),
                    mode=data.get('mode', 'unknown'),
                    status=data.get('status', 'unknown'),
                    startedAt=data.get('startedAt'),
                    finishedAt=data.get('finishedAt'),
                    executionTime=data.get('executionTime')
                )
            
            return None
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.get_execution_status")
            raise
    
    async def list_executions(self, workflow_id: Optional[str] = None, limit: int = 20) -> List[N8nExecution]:
        """List recent executions."""
        try:
            params = {'limit': limit}
            if workflow_id:
                params['workflowId'] = workflow_id
            
            data = await self._make_request('GET', '/executions', params=params)
            executions = []
            
            for exec_data in data.get('data', []):
                executions.append(N8nExecution(
                    id=str(exec_data['id']),
                    workflowId=str(exec_data.get('workflowId', '')),
                    mode=exec_data.get('mode', 'unknown'),
                    status=exec_data.get('status', 'unknown'),
                    startedAt=exec_data.get('startedAt'),
                    finishedAt=exec_data.get('finishedAt'),
                    executionTime=exec_data.get('executionTime')
                ))
            
            brebot_logger.log_agent_action(
                agent_name="N8nService",
                action="executions_listed",
                details={"count": len(executions), "workflow_id": workflow_id}
            )
            
            return executions
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.list_executions")
            raise
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow."""
        try:
            await self._make_request(
                'PATCH', 
                f'/workflows/{workflow_id}',
                json={'active': True}
            )
            
            brebot_logger.log_agent_action(
                agent_name="N8nService",
                action="workflow_activated",
                details={"workflow_id": workflow_id}
            )
            
            return True
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.activate_workflow")
            raise
    
    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow."""
        try:
            await self._make_request(
                'PATCH', 
                f'/workflows/{workflow_id}',
                json={'active': False}
            )
            
            brebot_logger.log_agent_action(
                agent_name="N8nService",
                action="workflow_deactivated",
                details={"workflow_id": workflow_id}
            )
            
            return True
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.deactivate_workflow")
            raise
    
    async def create_workflow(self, name: str, nodes: List[Dict] = None, tags: List[str] = None) -> Optional[N8nWorkflow]:
        """Create a new workflow."""
        try:
            workflow_data = {
                "name": name,
                "active": False,
                "nodes": nodes or [],
                "connections": {},
                "tags": tags or []
            }
            
            data = await self._make_request('POST', '/workflows', json=workflow_data)
            
            if data:
                workflow = N8nWorkflow(
                    id=str(data['id']),
                    name=data['name'],
                    active=data.get('active', False),
                    tags=data.get('tags', []),
                    createdAt=data.get('createdAt', ''),
                    updatedAt=data.get('updatedAt', ''),
                    nodes=len(data.get('nodes', []))
                )
                
                brebot_logger.log_agent_action(
                    agent_name="N8nService",
                    action="workflow_created",
                    details={"workflow_id": workflow.id, "name": name}
                )
                
                return workflow
            
            return None
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.create_workflow")
            raise
    
    async def update_workflow(self, workflow_id: str, name: Optional[str] = None, 
                             nodes: Optional[List[Dict]] = None, 
                             tags: Optional[List[str]] = None) -> Optional[N8nWorkflow]:
        """Update an existing workflow."""
        try:
            # Get current workflow
            current = await self.get_workflow(workflow_id)
            if not current:
                return None
            
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if nodes is not None:
                update_data['nodes'] = nodes
                update_data['connections'] = {}  # Reset connections when updating nodes
            if tags is not None:
                update_data['tags'] = tags
            
            if not update_data:
                return current  # No changes
            
            data = await self._make_request('PATCH', f'/workflows/{workflow_id}', json=update_data)
            
            if data:
                workflow = N8nWorkflow(
                    id=str(data['id']),
                    name=data['name'],
                    active=data.get('active', False),
                    tags=data.get('tags', []),
                    createdAt=data.get('createdAt', ''),
                    updatedAt=data.get('updatedAt', ''),
                    nodes=len(data.get('nodes', []))
                )
                
                brebot_logger.log_agent_action(
                    agent_name="N8nService",
                    action="workflow_updated",
                    details={"workflow_id": workflow_id, "changes": list(update_data.keys())}
                )
                
                return workflow
            
            return None
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.update_workflow")
            raise
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        try:
            await self._make_request('DELETE', f'/workflows/{workflow_id}')
            
            brebot_logger.log_agent_action(
                agent_name="N8nService",
                action="workflow_deleted",
                details={"workflow_id": workflow_id}
            )
            
            return True
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.delete_workflow")
            raise
    
    async def duplicate_workflow(self, workflow_id: str, new_name: Optional[str] = None) -> Optional[N8nWorkflow]:
        """Duplicate an existing workflow."""
        try:
            # Get the original workflow
            original = await self._make_request('GET', f'/workflows/{workflow_id}')
            if not original:
                return None
            
            # Create new workflow data
            duplicate_data = {
                "name": new_name or f"{original['name']} (Copy)",
                "active": False,  # Always create inactive copies
                "nodes": original.get('nodes', []),
                "connections": original.get('connections', {}),
                "tags": original.get('tags', [])
            }
            
            data = await self._make_request('POST', '/workflows', json=duplicate_data)
            
            if data:
                workflow = N8nWorkflow(
                    id=str(data['id']),
                    name=data['name'],
                    active=data.get('active', False),
                    tags=data.get('tags', []),
                    createdAt=data.get('createdAt', ''),
                    updatedAt=data.get('updatedAt', ''),
                    nodes=len(data.get('nodes', []))
                )
                
                brebot_logger.log_agent_action(
                    agent_name="N8nService",
                    action="workflow_duplicated",
                    details={"original_id": workflow_id, "new_id": workflow.id}
                )
                
                return workflow
            
            return None
            
        except Exception as e:
            brebot_logger.log_error(e, context="N8nService.duplicate_workflow")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check n8n instance health."""
        try:
            # Try to list workflows as a health check
            await self._make_request('GET', '/workflows', params={'limit': 1})
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy", 
                "base_url": self.base_url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global n8n service instance
n8n_service: Optional[N8nService] = None

def initialize_n8n_service(base_url: str, api_key: Optional[str] = None) -> N8nService:
    """Initialize the global n8n service instance."""
    global n8n_service
    n8n_service = N8nService(base_url, api_key)
    return n8n_service

def get_n8n_service() -> Optional[N8nService]:
    """Get the global n8n service instance."""
    return n8n_service