"""
Dropbox Integration Service for BreBot
Provides comprehensive file management and synchronization capabilities
"""

import asyncio
import io
import logging
from typing import Any, Dict, List, Optional, BinaryIO
from datetime import datetime
import hashlib
from pathlib import Path

import dropbox
from dropbox.exceptions import AuthError, ApiError
from pydantic import BaseModel

from utils.logger import brebot_logger
from services.activity_logger import log_platform_activity, Platform, ActivityType


class DropboxFile(BaseModel):
    """Dropbox file metadata model."""
    path: str
    name: str
    size: int
    modified: str
    is_folder: bool
    content_hash: Optional[str] = None
    shared_link: Optional[str] = None


class DropboxService:
    """Service for managing Dropbox files and folders."""
    
    def __init__(self, access_token: str):
        """
        Initialize Dropbox service.
        
        Args:
            access_token: Dropbox API access token
        """
        self.access_token = access_token
        self.client = dropbox.Dropbox(access_token)
        
        brebot_logger.log_agent_action(
            agent_name="DropboxService",
            action="initialized",
            details={"has_token": bool(access_token)}
        )
    
    async def list_files(self, path: str = "", recursive: bool = False, agent_name: str = "DropboxService") -> List[DropboxFile]:
        """List files and folders in Dropbox."""
        try:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Listing files in path: {path or '/'}"
            )
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._list_files_sync, path, recursive)
            
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully listed {len(result)} items",
                details={"path": path, "count": len(result), "recursive": recursive}
            )
            
            return result
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to list files",
                success=False,
                error_message=str(e),
                details={"path": path}
            )
            brebot_logger.log_error(e, context="DropboxService.list_files")
            raise
    
    def _list_files_sync(self, path: str, recursive: bool) -> List[DropboxFile]:
        """Synchronous file listing implementation."""
        files = []
        
        try:
            # Ensure path starts with /
            if path and not path.startswith('/'):
                path = f'/{path}'
            
            result = self.client.files_list_folder(path or '', recursive=recursive)
            
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    files.append(DropboxFile(
                        path=entry.path_display,
                        name=entry.name,
                        size=entry.size,
                        modified=entry.client_modified.isoformat(),
                        is_folder=False,
                        content_hash=entry.content_hash
                    ))
                elif isinstance(entry, dropbox.files.FolderMetadata):
                    files.append(DropboxFile(
                        path=entry.path_display,
                        name=entry.name,
                        size=0,
                        modified="",
                        is_folder=True
                    ))
            
            # Handle pagination
            while result.has_more:
                result = self.client.files_list_folder_continue(result.cursor)
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        files.append(DropboxFile(
                            path=entry.path_display,
                            name=entry.name,
                            size=entry.size,
                            modified=entry.client_modified.isoformat(),
                            is_folder=False,
                            content_hash=entry.content_hash
                        ))
                    elif isinstance(entry, dropbox.files.FolderMetadata):
                        files.append(DropboxFile(
                            path=entry.path_display,
                            name=entry.name,
                            size=0,
                            modified="",
                            is_folder=True
                        ))
            
            return files
            
        except ApiError as e:
            raise Exception(f"Dropbox API error: {e}")
    
    async def download_file(self, dropbox_path: str, local_path: Optional[str] = None, agent_name: str = "DropboxService") -> str:
        """Download a file from Dropbox."""
        try:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.DOWNLOAD,
                agent_name=agent_name,
                description=f"Starting download: {dropbox_path}",
                resource_path=dropbox_path
            )
            
            # Ensure path starts with /
            if not dropbox_path.startswith('/'):
                dropbox_path = f'/{dropbox_path}'
            
            # Generate local path if not provided
            if not local_path:
                local_path = f"downloads/dropbox{dropbox_path}"
            
            # Ensure local directory exists
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Run download in thread pool
            loop = asyncio.get_event_loop()
            file_size = await loop.run_in_executor(None, self._download_file_sync, dropbox_path, local_path)
            
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.DOWNLOAD,
                agent_name=agent_name,
                description=f"Successfully downloaded file to {local_path}",
                resource_path=dropbox_path,
                data_size=file_size,
                details={"local_path": local_path}
            )
            
            return local_path
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.DOWNLOAD,
                agent_name=agent_name,
                description="Failed to download file",
                resource_path=dropbox_path,
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="DropboxService.download_file")
            raise
    
    def _download_file_sync(self, dropbox_path: str, local_path: str) -> int:
        """Synchronous file download implementation."""
        try:
            metadata, response = self.client.files_download(dropbox_path)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return metadata.size
            
        except ApiError as e:
            raise Exception(f"Dropbox download error: {e}")
    
    async def upload_file(self, local_path: str, dropbox_path: str, overwrite: bool = True, agent_name: str = "DropboxService") -> DropboxFile:
        """Upload a file to Dropbox."""
        try:
            # Get file size for logging
            file_size = Path(local_path).stat().st_size
            
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.UPLOAD,
                agent_name=agent_name,
                description=f"Starting upload: {local_path} -> {dropbox_path}",
                resource_path=dropbox_path,
                data_size=file_size
            )
            
            # Ensure dropbox path starts with /
            if not dropbox_path.startswith('/'):
                dropbox_path = f'/{dropbox_path}'
            
            # Run upload in thread pool
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(None, self._upload_file_sync, local_path, dropbox_path, overwrite)
            
            dropbox_file = DropboxFile(
                path=metadata.path_display,
                name=metadata.name,
                size=metadata.size,
                modified=metadata.client_modified.isoformat(),
                is_folder=False,
                content_hash=metadata.content_hash
            )
            
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.UPLOAD,
                agent_name=agent_name,
                description=f"Successfully uploaded file",
                resource_path=dropbox_path,
                data_size=file_size,
                details={"local_path": local_path, "overwrite": overwrite}
            )
            
            return dropbox_file
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.UPLOAD,
                agent_name=agent_name,
                description="Failed to upload file",
                resource_path=dropbox_path,
                success=False,
                error_message=str(e),
                details={"local_path": local_path}
            )
            brebot_logger.log_error(e, context="DropboxService.upload_file")
            raise
    
    def _upload_file_sync(self, local_path: str, dropbox_path: str, overwrite: bool):
        """Synchronous file upload implementation."""
        try:
            mode = dropbox.files.WriteMode.overwrite if overwrite else dropbox.files.WriteMode.add
            
            with open(local_path, 'rb') as f:
                # For large files, use upload session
                file_size = Path(local_path).stat().st_size
                
                if file_size <= 150 * 1024 * 1024:  # 150MB limit for regular upload
                    metadata = self.client.files_upload(f.read(), dropbox_path, mode=mode, autorename=not overwrite)
                else:
                    # Use upload session for large files
                    upload_session = self.client.files_upload_session_start(f.read(8 * 1024 * 1024))  # 8MB chunks
                    cursor = dropbox.files.UploadSessionCursor(upload_session.session_id, f.tell())
                    
                    while f.tell() < file_size:
                        chunk = f.read(8 * 1024 * 1024)
                        if len(chunk) <= 8 * 1024 * 1024:
                            # Last chunk
                            commit = dropbox.files.CommitInfo(path=dropbox_path, mode=mode, autorename=not overwrite)
                            metadata = self.client.files_upload_session_finish(chunk, cursor, commit)
                            break
                        else:
                            self.client.files_upload_session_append_v2(chunk, cursor)
                            cursor.offset = f.tell()
            
            return metadata
            
        except ApiError as e:
            raise Exception(f"Dropbox upload error: {e}")
    
    async def create_folder(self, path: str, agent_name: str = "DropboxService") -> DropboxFile:
        """Create a new folder in Dropbox."""
        try:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Creating folder: {path}",
                resource_path=path
            )
            
            # Ensure path starts with /
            if not path.startswith('/'):
                path = f'/{path}'
            
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(None, self._create_folder_sync, path)
            
            folder = DropboxFile(
                path=metadata.path_display,
                name=metadata.name,
                size=0,
                modified="",
                is_folder=True
            )
            
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Successfully created folder",
                resource_path=path
            )
            
            return folder
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description="Failed to create folder",
                resource_path=path,
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="DropboxService.create_folder")
            raise
    
    def _create_folder_sync(self, path: str):
        """Synchronous folder creation implementation."""
        try:
            return self.client.files_create_folder_v2(path).metadata
        except ApiError as e:
            raise Exception(f"Dropbox folder creation error: {e}")
    
    async def delete_file(self, path: str, agent_name: str = "DropboxService") -> bool:
        """Delete a file or folder from Dropbox."""
        try:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description=f"Deleting: {path}",
                resource_path=path
            )
            
            # Ensure path starts with /
            if not path.startswith('/'):
                path = f'/{path}'
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._delete_file_sync, path)
            
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description=f"Successfully deleted",
                resource_path=path
            )
            
            return True
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description="Failed to delete",
                resource_path=path,
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="DropboxService.delete_file")
            raise
    
    def _delete_file_sync(self, path: str):
        """Synchronous file deletion implementation."""
        try:
            self.client.files_delete_v2(path)
        except ApiError as e:
            raise Exception(f"Dropbox deletion error: {e}")
    
    async def create_shared_link(self, path: str, agent_name: str = "DropboxService") -> str:
        """Create a shared link for a file or folder."""
        try:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Creating shared link for: {path}",
                resource_path=path
            )
            
            # Ensure path starts with /
            if not path.startswith('/'):
                path = f'/{path}'
            
            loop = asyncio.get_event_loop()
            link = await loop.run_in_executor(None, self._create_shared_link_sync, path)
            
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Successfully created shared link",
                resource_path=path,
                details={"shared_link": link}
            )
            
            return link
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description="Failed to create shared link",
                resource_path=path,
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="DropboxService.create_shared_link")
            raise
    
    def _create_shared_link_sync(self, path: str) -> str:
        """Synchronous shared link creation implementation."""
        try:
            # Check if link already exists
            try:
                links = self.client.sharing_list_shared_links(path=path, direct_only=True)
                if links.links:
                    return links.links[0].url
            except:
                pass  # Link doesn't exist, create new one
            
            # Create new shared link
            settings = dropbox.sharing.SharedLinkSettings(
                requested_visibility=dropbox.sharing.RequestedVisibility.public
            )
            link = self.client.sharing_create_shared_link_with_settings(path, settings)
            return link.url
            
        except ApiError as e:
            raise Exception(f"Dropbox shared link error: {e}")
    
    async def search_files(self, query: str, path: str = "", agent_name: str = "DropboxService") -> List[DropboxFile]:
        """Search for files in Dropbox."""
        try:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Searching for: {query}",
                details={"query": query, "path": path}
            )
            
            # Ensure path starts with /
            if path and not path.startswith('/'):
                path = f'/{path}'
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self._search_files_sync, query, path)
            
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Found {len(results)} files matching search",
                details={"query": query, "results_count": len(results)}
            )
            
            return results
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Search failed",
                success=False,
                error_message=str(e),
                details={"query": query}
            )
            brebot_logger.log_error(e, context="DropboxService.search_files")
            raise
    
    def _search_files_sync(self, query: str, path: str) -> List[DropboxFile]:
        """Synchronous file search implementation."""
        try:
            search_options = dropbox.files.SearchOptions(
                path=path or '',
                max_results=100
            )
            
            result = self.client.files_search_v2(query, options=search_options)
            
            files = []
            for match in result.matches:
                metadata = match.metadata.get_metadata()
                if isinstance(metadata, dropbox.files.FileMetadata):
                    files.append(DropboxFile(
                        path=metadata.path_display,
                        name=metadata.name,
                        size=metadata.size,
                        modified=metadata.client_modified.isoformat(),
                        is_folder=False,
                        content_hash=metadata.content_hash
                    ))
                elif isinstance(metadata, dropbox.files.FolderMetadata):
                    files.append(DropboxFile(
                        path=metadata.path_display,
                        name=metadata.name,
                        size=0,
                        modified="",
                        is_folder=True
                    ))
            
            return files
            
        except ApiError as e:
            raise Exception(f"Dropbox search error: {e}")
    
    async def get_account_info(self, agent_name: str = "DropboxService") -> Dict[str, Any]:
        """Get Dropbox account information."""
        try:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Getting account information"
            )
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, self._get_account_info_sync)
            
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Successfully retrieved account information",
                details={"account_id": info.get("account_id")}
            )
            
            return info
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.DROPBOX,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to get account information",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="DropboxService.get_account_info")
            raise
    
    def _get_account_info_sync(self) -> Dict[str, Any]:
        """Synchronous account info retrieval."""
        try:
            account = self.client.users_get_current_account()
            space_usage = self.client.users_get_space_usage()
            
            return {
                "account_id": account.account_id,
                "email": account.email,
                "name": account.name.display_name,
                "country": account.country,
                "locale": account.locale,
                "used_space": space_usage.used,
                "allocated_space": space_usage.allocation.get_individual().allocated if hasattr(space_usage.allocation, 'get_individual') else None,
                "account_type": account.account_type._tag
            }
            
        except ApiError as e:
            raise Exception(f"Dropbox account info error: {e}")


# Global Dropbox service instance
dropbox_service: Optional[DropboxService] = None

def initialize_dropbox_service(access_token: str) -> DropboxService:
    """Initialize the global Dropbox service instance."""
    global dropbox_service
    dropbox_service = DropboxService(access_token)
    return dropbox_service

def get_dropbox_service() -> Optional[DropboxService]:
    """Get the global Dropbox service instance."""
    return dropbox_service