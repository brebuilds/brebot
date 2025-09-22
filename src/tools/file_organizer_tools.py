"""
File Organizer Tools for Brebot.
Tools that the File Organizer Agent can use to manage files and directories.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ListFilesInput(BaseModel):
    """Input schema for list_files tool."""
    directory_path: str = Field(description="Path to the directory to list files from")
    include_hidden: bool = Field(default=False, description="Whether to include hidden files")
    file_extensions: Optional[List[str]] = Field(default=None, description="Filter by file extensions (e.g., ['.txt', '.pdf'])")
    recursive: bool = Field(default=False, description="Whether to search recursively in subdirectories")


class CreateFolderInput(BaseModel):
    """Input schema for create_folder tool."""
    folder_path: str = Field(description="Path where the new folder should be created")
    folder_name: str = Field(description="Name of the folder to create")


class MoveFileInput(BaseModel):
    """Input schema for move_file tool."""
    source_path: str = Field(description="Path to the file to move")
    destination_path: str = Field(description="Path where the file should be moved to")
    create_destination: bool = Field(default=True, description="Whether to create destination directory if it doesn't exist")
    backup: bool = Field(default=True, description="Whether to create a backup before moving")


class ListFilesTool(BaseTool):
    """Tool to list files in a specified directory."""
    
    name: str = "list_files"
    description: str = "List all files in a specified directory with optional filtering"
    args_schema: type[BaseModel] = ListFilesInput
    
    def _run(
        self, 
        directory_path: str, 
        include_hidden: bool = False, 
        file_extensions: Optional[List[str]] = None,
        recursive: bool = False
    ) -> str:
        """
        List files in the specified directory.
        
        Args:
            directory_path: Path to the directory
            include_hidden: Whether to include hidden files
            file_extensions: Filter by file extensions
            recursive: Whether to search recursively
            
        Returns:
            str: Formatted list of files with metadata
        """
        try:
            directory = Path(directory_path)
            
            if not directory.exists():
                return f"Error: Directory '{directory_path}' does not exist."
            
            if not directory.is_dir():
                return f"Error: '{directory_path}' is not a directory."
            
            files = []
            
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    # Skip hidden files if not requested
                    if not include_hidden and file_path.name.startswith('.'):
                        continue
                    
                    # Filter by extensions if specified
                    if file_extensions:
                        if file_path.suffix.lower() not in [ext.lower() for ext in file_extensions]:
                            continue
                    
                    # Get file metadata
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'extension': file_path.suffix
                    })
            
            if not files:
                return f"No files found in '{directory_path}' with the specified criteria."
            
            # Sort files by name
            files.sort(key=lambda x: x['name'])
            
            # Format output
            result = f"Found {len(files)} files in '{directory_path}':\n\n"
            for file_info in files:
                size_mb = file_info['size'] / (1024 * 1024)
                result += f"📄 {file_info['name']}\n"
                result += f"   Path: {file_info['path']}\n"
                result += f"   Size: {size_mb:.2f} MB\n"
                result += f"   Modified: {file_info['modified']}\n"
                result += f"   Extension: {file_info['extension']}\n\n"
            
            return result
            
        except PermissionError:
            return f"Error: Permission denied accessing '{directory_path}'."
        except Exception as e:
            return f"Error listing files in '{directory_path}': {str(e)}"


class CreateFolderTool(BaseTool):
    """Tool to create a new folder."""
    
    name: str = "create_folder"
    description: str = "Create a new folder at the specified path"
    args_schema: type[BaseModel] = CreateFolderInput
    
    def _run(self, folder_path: str, folder_name: str) -> str:
        """
        Create a new folder.
        
        Args:
            folder_path: Path where the folder should be created
            folder_name: Name of the folder to create
            
        Returns:
            str: Success or error message
        """
        try:
            base_path = Path(folder_path)
            new_folder_path = base_path / folder_name
            
            if not base_path.exists():
                return f"Error: Base directory '{folder_path}' does not exist."
            
            if not base_path.is_dir():
                return f"Error: '{folder_path}' is not a directory."
            
            if new_folder_path.exists():
                return f"Folder '{folder_name}' already exists at '{folder_path}'."
            
            # Create the folder
            new_folder_path.mkdir(parents=True, exist_ok=True)
            
            return f"✅ Successfully created folder '{folder_name}' at '{folder_path}'."
            
        except PermissionError:
            return f"Error: Permission denied creating folder in '{folder_path}'."
        except Exception as e:
            return f"Error creating folder '{folder_name}' in '{folder_path}': {str(e)}"


class MoveFileTool(BaseTool):
    """Tool to move a file to a new location."""
    
    name: str = "move_file"
    description: str = "Move a file from source to destination with optional backup"
    args_schema: type[BaseModel] = MoveFileInput
    
    def _run(
        self, 
        source_path: str, 
        destination_path: str, 
        create_destination: bool = True,
        backup: bool = True
    ) -> str:
        """
        Move a file to a new location.
        
        Args:
            source_path: Path to the file to move
            destination_path: Path where the file should be moved
            create_destination: Whether to create destination directory if it doesn't exist
            backup: Whether to create a backup before moving
            
        Returns:
            str: Success or error message
        """
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            # Validate source file
            if not source.exists():
                return f"Error: Source file '{source_path}' does not exist."
            
            if not source.is_file():
                return f"Error: '{source_path}' is not a file."
            
            # Handle destination directory
            if destination.is_dir():
                # If destination is a directory, move file into it
                final_destination = destination / source.name
            else:
                # If destination is a file path
                final_destination = destination
                dest_dir = destination.parent
                
                if create_destination and not dest_dir.exists():
                    dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if destination already exists
            if final_destination.exists():
                return f"Error: Destination '{final_destination}' already exists."
            
            # Create backup if requested
            if backup:
                backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / source.name
                shutil.copy2(source, backup_path)
                backup_msg = f" (backup created at {backup_path})"
            else:
                backup_msg = ""
            
            # Move the file
            shutil.move(str(source), str(final_destination))
            
            return f"✅ Successfully moved '{source_path}' to '{final_destination}'{backup_msg}."
            
        except PermissionError:
            return f"Error: Permission denied moving file from '{source_path}' to '{destination_path}'."
        except Exception as e:
            return f"Error moving file from '{source_path}' to '{destination_path}': {str(e)}"


class OrganizeFilesTool(BaseTool):
    """Tool to organize files by extension into folders."""
    
    name: str = "organize_files"
    description: str = "Organize files in a directory by creating folders based on file extensions"
    args_schema: type[BaseModel] = BaseModel
    
    def _run(self, directory_path: str, dry_run: bool = False) -> str:
        """
        Organize files by extension into folders.
        
        Args:
            directory_path: Path to the directory to organize
            dry_run: If True, only show what would be done without actually doing it
            
        Returns:
            str: Summary of organization actions
        """
        try:
            directory = Path(directory_path)
            
            if not directory.exists():
                return f"Error: Directory '{directory_path}' does not exist."
            
            if not directory.is_dir():
                return f"Error: '{directory_path}' is not a directory."
            
            # Get all files in the directory
            files = [f for f in directory.iterdir() if f.is_file()]
            
            if not files:
                return f"No files found in '{directory_path}' to organize."
            
            # Group files by extension
            extension_groups = {}
            for file in files:
                ext = file.suffix.lower() or 'no_extension'
                if ext not in extension_groups:
                    extension_groups[ext] = []
                extension_groups[ext].append(file)
            
            result = f"📁 Organization plan for '{directory_path}':\n\n"
            actions_taken = 0
            
            for ext, file_list in extension_groups.items():
                if len(file_list) <= 1:
                    continue  # Skip if only one file of this type
                
                # Create folder name
                folder_name = f"{ext[1:].upper()}_Files" if ext != 'no_extension' else "No_Extension_Files"
                folder_path = directory / folder_name
                
                result += f"📂 {folder_name} ({len(file_list)} files):\n"
                
                if not dry_run:
                    # Create folder if it doesn't exist
                    if not folder_path.exists():
                        folder_path.mkdir(exist_ok=True)
                        result += f"   ✅ Created folder: {folder_name}\n"
                    
                    # Move files
                    for file in file_list:
                        dest_path = folder_path / file.name
                        if not dest_path.exists():
                            shutil.move(str(file), str(dest_path))
                            result += f"   📄 Moved: {file.name}\n"
                            actions_taken += 1
                        else:
                            result += f"   ⚠️  Skipped (exists): {file.name}\n"
                else:
                    for file in file_list:
                        result += f"   📄 Would move: {file.name}\n"
                    actions_taken += len(file_list)
                
                result += "\n"
            
            if dry_run:
                result += f"🔍 DRY RUN: Would organize {actions_taken} files into {len(extension_groups)} folders.\n"
            else:
                result += f"✅ Successfully organized {actions_taken} files.\n"
            
            return result
            
        except Exception as e:
            return f"Error organizing files in '{directory_path}': {str(e)}"


# Export all tools
__all__ = [
    "ListFilesTool",
    "CreateFolderTool", 
    "MoveFileTool",
    "OrganizeFilesTool"
]
