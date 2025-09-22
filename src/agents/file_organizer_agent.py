"""
File Organizer Agent for Brebot.
An AI agent specialized in organizing files and directories.
"""

from typing import List, Optional
from crewai import Agent, Task, Crew, Process
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

from config import get_llm_config, get_embedding_config, settings
from tools import ListFilesTool, CreateFolderTool, MoveFileTool, OrganizeFilesTool
from utils import brebot_logger


class FileOrganizerAgent:
    """File Organizer Agent that can organize files and directories."""
    
    def __init__(self, llm_config: dict = None, embedding_config: dict = None):
        """
        Initialize the File Organizer Agent.
        
        Args:
            llm_config: LLM configuration dictionary
            embedding_config: Embedding configuration dictionary
        """
        self.llm_config = llm_config or get_llm_config(settings)
        self.embedding_config = embedding_config or get_embedding_config(settings)
        
        # Initialize LLM and embedding models
        self.llm = self._setup_llm()
        self.embedding = self._setup_embedding()
        
        # Initialize tools
        self.tools = self._setup_tools()
        
        # Create the agent
        self.agent = self._create_agent()
        
        brebot_logger.log_agent_action(
            agent_name="FileOrganizerAgent",
            action="initialized",
            details={
                "llm_provider": self.llm_config["provider"],
                "llm_model": self.llm_config["model"],
                "tools_count": len(self.tools)
            }
        )
    
    def _setup_llm(self):
        """Set up the LLM based on configuration."""
        if self.llm_config["provider"] == "ollama":
            return Ollama(
                model=self.llm_config["model"],
                base_url=self.llm_config["base_url"],
                temperature=0.1,
                request_timeout=120.0
            )
        else:
            # For OpenAI or other providers, you would set up accordingly
            raise ValueError(f"LLM provider '{self.llm_config['provider']}' not yet implemented")
    
    def _setup_embedding(self):
        """Set up the embedding model."""
        return OllamaEmbedding(
            model_name=self.embedding_config["model"],
            base_url=self.embedding_config["base_url"]
        )
    
    def _setup_tools(self) -> List:
        """Set up tools for the agent."""
        return [
            ListFilesTool(),
            CreateFolderTool(),
            MoveFileTool(),
            OrganizeFilesTool()
        ]
    
    def _create_agent(self) -> Agent:
        """Create the File Organizer Agent."""
        return Agent(
            role="File Organization Specialist",
            goal="""Efficiently organize files and directories by creating logical folder structures, 
            moving files to appropriate locations, and maintaining a clean, organized file system. 
            Always prioritize user productivity and file accessibility.""",
            
            backstory="""You are an expert file organization specialist with years of experience 
            helping businesses and individuals maintain clean, efficient file systems. You understand 
            the importance of logical folder structures, consistent naming conventions, and easy file 
            retrieval. You're meticulous about creating backups before making changes and always 
            explain your organizational decisions clearly. You excel at analyzing file types, 
            usage patterns, and user workflows to create the most effective organization system.""",
            
            verbose=settings.agent_verbose,
            allow_delegation=False,
            tools=self.tools,
            llm=self.llm,
            max_iter=settings.agent_max_iter,
            memory=settings.agent_memory,
            max_execution_time=300,  # 5 minutes max execution time
            
            # Custom instructions for file organization
            system_message="""You are a File Organization Specialist. When organizing files:

1. **Safety First**: Always create backups before moving files
2. **Logical Grouping**: Group files by type, project, date, or purpose
3. **Clear Naming**: Use descriptive folder names (e.g., "Documents_2024", "Project_Assets")
4. **User-Friendly**: Consider how users will find files later
5. **Efficient**: Minimize clicks and navigation steps
6. **Consistent**: Use consistent naming conventions throughout

When given a task:
- First, analyze the current file structure
- Identify patterns and logical groupings
- Propose an organization plan
- Execute the plan step by step
- Verify the results

Always explain your reasoning and ask for confirmation before making major changes."""
        )
    
    def organize_directory(self, directory_path: str, organization_type: str = "by_extension") -> str:
        """
        Organize files in a directory.
        
        Args:
            directory_path: Path to the directory to organize
            organization_type: Type of organization (by_extension, by_date, by_project)
            
        Returns:
            str: Result of the organization task
        """
        brebot_logger.log_agent_action(
            agent_name="FileOrganizerAgent",
            action="organize_directory",
            details={
                "directory_path": directory_path,
                "organization_type": organization_type
            }
        )
        
        # Create a task for organizing the directory
        task = Task(
            description=f"""
            Organize the files in the directory: {directory_path}
            
            Organization type: {organization_type}
            
            Please:
            1. First, list all files in the directory to understand the current structure
            2. Analyze the files and determine the best organization approach
            3. Create appropriate folders based on the organization type
            4. Move files to their appropriate locations
            5. Provide a summary of what was organized
            
            Make sure to:
            - Create backups before moving files
            - Use clear, descriptive folder names
            - Group related files together
            - Maintain a logical structure
            """,
            expected_output="""A detailed report including:
            - List of files found in the directory
            - Organization plan that was implemented
            - Summary of folders created
            - Summary of files moved
            - Any issues encountered or recommendations for future organization""",
            agent=self.agent
        )
        
        # Create a crew with the agent and task
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
            verbose=settings.agent_verbose
        )
        
        try:
            # Execute the task
            result = crew.kickoff()
            
            brebot_logger.log_crew_activity(
                crew_name="FileOrganizerCrew",
                activity="organize_directory_completed",
                details={
                    "directory_path": directory_path,
                    "organization_type": organization_type,
                    "success": True
                }
            )
            
            return str(result)
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"FileOrganizerAgent.organize_directory({directory_path})"
            )
            
            return f"Error organizing directory '{directory_path}': {str(e)}"
    
    def create_folder_structure(self, base_path: str, structure_description: str) -> str:
        """
        Create a folder structure based on a description.
        
        Args:
            base_path: Base path where to create the structure
            structure_description: Description of the desired folder structure
            
        Returns:
            str: Result of the folder creation task
        """
        brebot_logger.log_agent_action(
            agent_name="FileOrganizerAgent",
            action="create_folder_structure",
            details={
                "base_path": base_path,
                "structure_description": structure_description
            }
        )
        
        task = Task(
            description=f"""
            Create a folder structure at: {base_path}
            
            Structure description: {structure_description}
            
            Please:
            1. Analyze the structure description
            2. Create the necessary folders and subfolders
            3. Ensure proper nesting and organization
            4. Use clear, descriptive folder names
            5. Provide a summary of the created structure
            
            Make sure to:
            - Create folders in the correct order (parent folders first)
            - Use consistent naming conventions
            - Handle any special characters or spaces appropriately
            """,
            expected_output="""A detailed report including:
            - Analysis of the requested structure
            - List of folders created
            - Folder hierarchy diagram
            - Any recommendations for the structure""",
            agent=self.agent
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
            verbose=settings.agent_verbose
        )
        
        try:
            result = crew.kickoff()
            
            brebot_logger.log_crew_activity(
                crew_name="FileOrganizerCrew",
                activity="create_folder_structure_completed",
                details={
                    "base_path": base_path,
                    "structure_description": structure_description,
                    "success": True
                }
            )
            
            return str(result)
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"FileOrganizerAgent.create_folder_structure({base_path})"
            )
            
            return f"Error creating folder structure at '{base_path}': {str(e)}"
    
    def move_files_to_organized_structure(self, source_path: str, destination_base: str) -> str:
        """
        Move files from source to an organized destination structure.
        
        Args:
            source_path: Path to source files
            destination_base: Base path for organized destination
            
        Returns:
            str: Result of the file moving task
        """
        brebot_logger.log_agent_action(
            agent_name="FileOrganizerAgent",
            action="move_files_to_organized_structure",
            details={
                "source_path": source_path,
                "destination_base": destination_base
            }
        )
        
        task = Task(
            description=f"""
            Move files from: {source_path}
            To organized structure at: {destination_base}
            
            Please:
            1. List all files in the source path
            2. Analyze file types and determine appropriate destinations
            3. Create organized folder structure at destination if needed
            4. Move files to appropriate locations
            5. Create backups before moving
            6. Provide a summary of the move operation
            
            Make sure to:
            - Preserve file integrity
            - Create logical folder groupings
            - Handle duplicate files appropriately
            - Maintain file permissions and metadata
            """,
            expected_output="""A detailed report including:
            - List of source files analyzed
            - Organization plan implemented
            - Summary of files moved
            - New folder structure created
            - Any issues or conflicts resolved""",
            agent=self.agent
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
            verbose=settings.agent_verbose
        )
        
        try:
            result = crew.kickoff()
            
            brebot_logger.log_crew_activity(
                crew_name="FileOrganizerCrew",
                activity="move_files_to_organized_structure_completed",
                details={
                    "source_path": source_path,
                    "destination_base": destination_base,
                    "success": True
                }
            )
            
            return str(result)
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"FileOrganizerAgent.move_files_to_organized_structure({source_path}, {destination_base})"
            )
            
            return f"Error moving files from '{source_path}' to '{destination_base}': {str(e)}"


# Export the agent class
__all__ = ["FileOrganizerAgent"]
