"""
Enhanced Airtable Integration Service for BreBot
Provides comprehensive database management capabilities with activity logging
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import httpx
from pydantic import BaseModel

from utils.logger import brebot_logger
from services.activity_logger import log_platform_activity, Platform, ActivityType


class AirtableRecord(BaseModel):
    """Airtable record model."""
    id: str
    fields: Dict[str, Any]
    created_time: Optional[str] = None


class AirtableTable(BaseModel):
    """Airtable table metadata."""
    id: str
    name: str
    primary_field_id: Optional[str] = None
    fields: List[Dict[str, Any]] = []


class AirtableBase(BaseModel):
    """Airtable base metadata."""
    id: str
    name: str
    permission_level: str
    tables: List[AirtableTable] = []


class AirtableService:
    """Enhanced service for managing Airtable bases, tables, and records."""
    
    def __init__(self, api_key: str):
        """
        Initialize Airtable service.
        
        Args:
            api_key: Airtable API key
        """
        self.api_key = api_key
        self.base_url = "https://api.airtable.com/v0"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        brebot_logger.log_agent_action(
            agent_name="AirtableService",
            action="initialized",
            details={"has_api_key": bool(api_key)}
        )
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Airtable API."""
        url = f"{self.base_url}{endpoint}"
        
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
                    context=f"AirtableService._make_request",
                    details={"method": method, "endpoint": endpoint, "status": getattr(e.response, 'status_code', None)}
                )
                raise Exception(f"Airtable API error: {e}")
    
    async def list_bases(self, agent_name: str = "AirtableService") -> List[AirtableBase]:
        """List all accessible Airtable bases."""
        try:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Listing accessible bases"
            )
            
            data = await self._make_request('GET', '/meta/bases')
            bases = []
            
            for base_data in data.get('bases', []):
                base = AirtableBase(
                    id=base_data['id'],
                    name=base_data['name'],
                    permission_level=base_data['permissionLevel']
                )
                bases.append(base)
            
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully listed {len(bases)} bases",
                details={"bases_count": len(bases)}
            )
            
            return bases
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to list bases",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="AirtableService.list_bases")
            raise
    
    async def get_base_schema(self, base_id: str, agent_name: str = "AirtableService") -> AirtableBase:
        """Get base schema including tables and fields."""
        try:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Getting schema for base: {base_id}",
                resource_id=base_id
            )
            
            data = await self._make_request('GET', f'/meta/bases/{base_id}/tables')
            
            tables = []
            for table_data in data.get('tables', []):
                table = AirtableTable(
                    id=table_data['id'],
                    name=table_data['name'],
                    primary_field_id=table_data.get('primaryFieldId'),
                    fields=table_data.get('fields', [])
                )
                tables.append(table)
            
            base = AirtableBase(
                id=base_id,
                name=data.get('name', base_id),
                permission_level="read",  # Default
                tables=tables
            )
            
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved schema with {len(tables)} tables",
                resource_id=base_id,
                details={"tables_count": len(tables)}
            )
            
            return base
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to get base schema",
                resource_id=base_id,
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="AirtableService.get_base_schema")
            raise
    
    async def list_records(
        self, 
        base_id: str, 
        table_id: str, 
        max_records: int = 100,
        view: Optional[str] = None,
        filter_formula: Optional[str] = None,
        agent_name: str = "AirtableService"
    ) -> List[AirtableRecord]:
        """List records from a table."""
        try:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Listing records from table: {table_id}",
                resource_id=f"{base_id}/{table_id}",
                details={"max_records": max_records, "view": view, "filter": filter_formula}
            )
            
            params = {"maxRecords": max_records}
            if view:
                params["view"] = view
            if filter_formula:
                params["filterByFormula"] = filter_formula
            
            data = await self._make_request('GET', f'/{base_id}/{table_id}', params=params)
            
            records = []
            for record_data in data.get('records', []):
                record = AirtableRecord(
                    id=record_data['id'],
                    fields=record_data.get('fields', {}),
                    created_time=record_data.get('createdTime')
                )
                records.append(record)
            
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved {len(records)} records",
                resource_id=f"{base_id}/{table_id}",
                details={"records_count": len(records)}
            )
            
            return records
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to list records",
                resource_id=f"{base_id}/{table_id}",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="AirtableService.list_records")
            raise
    
    async def create_record(
        self, 
        base_id: str, 
        table_id: str, 
        fields: Dict[str, Any],
        agent_name: str = "AirtableService"
    ) -> AirtableRecord:
        """Create a new record in a table."""
        try:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Creating record in table: {table_id}",
                resource_id=f"{base_id}/{table_id}",
                details={"fields": list(fields.keys())}
            )
            
            payload = {
                "fields": fields
            }
            
            data = await self._make_request('POST', f'/{base_id}/{table_id}', json=payload)
            
            record = AirtableRecord(
                id=data['id'],
                fields=data.get('fields', {}),
                created_time=data.get('createdTime')
            )
            
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Successfully created record: {record.id}",
                resource_id=f"{base_id}/{table_id}/{record.id}",
                details={"record_id": record.id, "fields_created": list(fields.keys())}
            )
            
            return record
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description="Failed to create record",
                resource_id=f"{base_id}/{table_id}",
                success=False,
                error_message=str(e),
                details={"attempted_fields": list(fields.keys())}
            )
            brebot_logger.log_error(e, context="AirtableService.create_record")
            raise
    
    async def update_record(
        self, 
        base_id: str, 
        table_id: str, 
        record_id: str, 
        fields: Dict[str, Any],
        agent_name: str = "AirtableService"
    ) -> AirtableRecord:
        """Update an existing record."""
        try:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description=f"Updating record: {record_id}",
                resource_id=f"{base_id}/{table_id}/{record_id}",
                details={"fields_updated": list(fields.keys())}
            )
            
            payload = {
                "fields": fields
            }
            
            data = await self._make_request('PATCH', f'/{base_id}/{table_id}/{record_id}', json=payload)
            
            record = AirtableRecord(
                id=data['id'],
                fields=data.get('fields', {}),
                created_time=data.get('createdTime')
            )
            
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description=f"Successfully updated record",
                resource_id=f"{base_id}/{table_id}/{record_id}",
                details={"fields_updated": list(fields.keys())}
            )
            
            return record
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description="Failed to update record",
                resource_id=f"{base_id}/{table_id}/{record_id}",
                success=False,
                error_message=str(e),
                details={"attempted_fields": list(fields.keys())}
            )
            brebot_logger.log_error(e, context="AirtableService.update_record")
            raise
    
    async def delete_record(
        self, 
        base_id: str, 
        table_id: str, 
        record_id: str,
        agent_name: str = "AirtableService"
    ) -> bool:
        """Delete a record from a table."""
        try:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description=f"Deleting record: {record_id}",
                resource_id=f"{base_id}/{table_id}/{record_id}"
            )
            
            await self._make_request('DELETE', f'/{base_id}/{table_id}/{record_id}')
            
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description=f"Successfully deleted record",
                resource_id=f"{base_id}/{table_id}/{record_id}"
            )
            
            return True
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description="Failed to delete record",
                resource_id=f"{base_id}/{table_id}/{record_id}",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="AirtableService.delete_record")
            raise
    
    async def batch_create_records(
        self, 
        base_id: str, 
        table_id: str, 
        records_data: List[Dict[str, Any]],
        agent_name: str = "AirtableService"
    ) -> List[AirtableRecord]:
        """Create multiple records in a single batch operation."""
        try:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Batch creating {len(records_data)} records",
                resource_id=f"{base_id}/{table_id}",
                details={"batch_size": len(records_data)}
            )
            
            # Airtable allows max 10 records per batch
            batch_size = 10
            all_records = []
            
            for i in range(0, len(records_data), batch_size):
                batch = records_data[i:i + batch_size]
                payload = {
                    "records": [{"fields": record_fields} for record_fields in batch]
                }
                
                data = await self._make_request('POST', f'/{base_id}/{table_id}', json=payload)
                
                for record_data in data.get('records', []):
                    record = AirtableRecord(
                        id=record_data['id'],
                        fields=record_data.get('fields', {}),
                        created_time=record_data.get('createdTime')
                    )
                    all_records.append(record)
            
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Successfully batch created {len(all_records)} records",
                resource_id=f"{base_id}/{table_id}",
                details={"records_created": len(all_records)}
            )
            
            return all_records
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description="Failed to batch create records",
                resource_id=f"{base_id}/{table_id}",
                success=False,
                error_message=str(e),
                details={"attempted_batch_size": len(records_data)}
            )
            brebot_logger.log_error(e, context="AirtableService.batch_create_records")
            raise
    
    async def search_records(
        self, 
        base_id: str, 
        table_id: str, 
        search_term: str,
        search_fields: Optional[List[str]] = None,
        agent_name: str = "AirtableService"
    ) -> List[AirtableRecord]:
        """Search for records containing a specific term."""
        try:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Searching records for: {search_term}",
                resource_id=f"{base_id}/{table_id}",
                details={"search_term": search_term, "search_fields": search_fields}
            )
            
            # Build filter formula for search
            if search_fields:
                # Search in specific fields
                field_conditions = []
                for field in search_fields:
                    field_conditions.append(f"FIND(LOWER('{search_term}'), LOWER(CONCATENATE({{{field}}}, '')))")
                filter_formula = f"OR({', '.join(field_conditions)})"
            else:
                # Search in all text fields (simplified approach)
                filter_formula = f"SEARCH(LOWER('{search_term}'), LOWER(CONCATENATE(RECORD_ID(), ' ')))"
            
            records = await self.list_records(
                base_id=base_id,
                table_id=table_id,
                filter_formula=filter_formula,
                max_records=100,
                agent_name=agent_name
            )
            
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Search found {len(records)} matching records",
                resource_id=f"{base_id}/{table_id}",
                details={"search_term": search_term, "results_count": len(records)}
            )
            
            return records
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Search failed",
                resource_id=f"{base_id}/{table_id}",
                success=False,
                error_message=str(e),
                details={"search_term": search_term}
            )
            brebot_logger.log_error(e, context="AirtableService.search_records")
            raise
    
    async def export_table_data(
        self, 
        base_id: str, 
        table_id: str,
        format_type: str = "json",
        agent_name: str = "AirtableService"
    ) -> str:
        """Export all data from a table."""
        try:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Exporting table data in {format_type} format",
                resource_id=f"{base_id}/{table_id}",
                details={"format": format_type}
            )
            
            # Get all records (with pagination)
            all_records = []
            offset = None
            
            while True:
                params = {"maxRecords": 100}
                if offset:
                    params["offset"] = offset
                
                data = await self._make_request('GET', f'/{base_id}/{table_id}', params=params)
                
                for record_data in data.get('records', []):
                    record = AirtableRecord(
                        id=record_data['id'],
                        fields=record_data.get('fields', {}),
                        created_time=record_data.get('createdTime')
                    )
                    all_records.append(record)
                
                offset = data.get('offset')
                if not offset:
                    break
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"airtable_export_{base_id}_{table_id}_{timestamp}.{format_type}"
            filepath = f"exports/{filename}"
            
            # Ensure exports directory exists
            import os
            os.makedirs("exports", exist_ok=True)
            
            if format_type == "json":
                data_to_export = [record.dict() for record in all_records]
                with open(filepath, 'w') as f:
                    json.dump(data_to_export, f, indent=2, default=str)
            elif format_type == "csv":
                import csv
                if all_records:
                    # Get all unique field names
                    all_fields = set()
                    for record in all_records:
                        all_fields.update(record.fields.keys())
                    
                    with open(filepath, 'w', newline='') as f:
                        writer = csv.writer(f)
                        # Write header
                        writer.writerow(['id', 'created_time'] + list(all_fields))
                        
                        # Write data
                        for record in all_records:
                            row = [record.id, record.created_time]
                            for field in all_fields:
                                value = record.fields.get(field, '')
                                # Convert complex values to JSON strings
                                if isinstance(value, (dict, list)):
                                    value = json.dumps(value)
                                row.append(value)
                            writer.writerow(row)
            
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully exported {len(all_records)} records to {filepath}",
                resource_id=f"{base_id}/{table_id}",
                details={"records_exported": len(all_records), "file_path": filepath}
            )
            
            return filepath
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.AIRTABLE,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Export failed",
                resource_id=f"{base_id}/{table_id}",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="AirtableService.export_table_data")
            raise


# Global Airtable service instance
airtable_service: Optional[AirtableService] = None

def initialize_airtable_service(api_key: str) -> AirtableService:
    """Initialize the global Airtable service instance."""
    global airtable_service
    airtable_service = AirtableService(api_key)
    return airtable_service

def get_airtable_service() -> Optional[AirtableService]:
    """Get the global Airtable service instance."""
    return airtable_service