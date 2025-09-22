"""
Main Brebot Crew Definition.
Orchestrates all agents and manages the overall system workflow.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from datetime import datetime

from crewai import Crew, Process
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

from config import get_llm_config, get_embedding_config, settings
from agents import FileOrganizerAgent, MarketingAgent, WebDesignAgent
from utils import brebot_logger


class BrebotCrew:
    """Main Brebot crew that orchestrates all agents and workflows."""
    
    def __init__(self, llm_config: dict = None, embedding_config: dict = None):
        """
        Initialize the Brebot crew.
        
        Args:
            llm_config: LLM configuration dictionary
            embedding_config: Embedding configuration dictionary
        """
        self.llm_config = llm_config or get_llm_config(settings)
        self.embedding_config = embedding_config or get_embedding_config(settings)
        
        # Initialize LLM and embedding models
        self.llm = self._setup_llm()
        self.embedding = self._setup_embedding()
        
        # Initialize agents
        self.agents = self._setup_agents()
        
        # Initialize the crew
        self.crew = self._create_crew()
        
        brebot_logger.log_crew_activity(
            crew_name="BrebotCrew",
            activity="initialized",
            details={
                "llm_provider": self.llm_config["provider"],
                "llm_model": self.llm_config["model"],
                "agents_count": len(self.agents)
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
            raise ValueError(f"LLM provider '{self.llm_config['provider']}' not yet implemented")
    
    def _setup_embedding(self):
        """Set up the embedding model."""
        return OllamaEmbedding(
            model_name=self.embedding_config["model"],
            base_url=self.embedding_config["base_url"]
        )
    
    def _setup_agents(self) -> Dict[str, Any]:
        """Set up all agents for the crew."""
        agents = {}
        
        # File Organizer Agent
        agents["file_organizer"] = FileOrganizerAgent(
            llm_config=self.llm_config,
            embedding_config=self.embedding_config
        )
        
        # Marketing Agent
        agents["marketing"] = MarketingAgent(
            llm_config=self.llm_config,
            embedding_config=self.embedding_config
        )
        
        # Web Design Agent
        agents["web_design"] = WebDesignAgent(
            llm_config=self.llm_config,
            embedding_config=self.embedding_config
        )
        
        return agents
    
    def _create_crew(self) -> Crew:
        """Create the main crew with all agents."""
        return Crew(
            agents=list(self.agents.values()),
            process=Process.sequential,
            verbose=settings.agent_verbose,
            memory=settings.agent_memory,
            planning=True,  # Enable planning for complex tasks
            embedder=self.embedding
        )
    
    def organize_files(self, directory_path: str, organization_type: str = "by_extension") -> str:
        """
        Organize files in a directory using the File Organizer Agent.
        
        Args:
            directory_path: Path to the directory to organize
            organization_type: Type of organization to perform
            
        Returns:
            str: Result of the organization task
        """
        brebot_logger.log_crew_activity(
            crew_name="BrebotCrew",
            activity="organize_files_started",
            details={
                "directory_path": directory_path,
                "organization_type": organization_type
            }
        )
        
        try:
            result = self.agents["file_organizer"].organize_directory(
                directory_path=directory_path,
                organization_type=organization_type
            )
            
            brebot_logger.log_crew_activity(
                crew_name="BrebotCrew",
                activity="organize_files_completed",
                details={
                    "directory_path": directory_path,
                    "organization_type": organization_type,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"BrebotCrew.organize_files({directory_path})"
            )
            
            return f"Error organizing files: {str(e)}"
    
    def create_folder_structure(self, base_path: str, structure_description: str) -> str:
        """
        Create a folder structure using the File Organizer Agent.
        
        Args:
            base_path: Base path where to create the structure
            structure_description: Description of the desired folder structure
            
        Returns:
            str: Result of the folder creation task
        """
        brebot_logger.log_crew_activity(
            crew_name="BrebotCrew",
            activity="create_folder_structure_started",
            details={
                "base_path": base_path,
                "structure_description": structure_description
            }
        )
        
        try:
            result = self.agents["file_organizer"].create_folder_structure(
                base_path=base_path,
                structure_description=structure_description
            )
            
            brebot_logger.log_crew_activity(
                crew_name="BrebotCrew",
                activity="create_folder_structure_completed",
                details={
                    "base_path": base_path,
                    "structure_description": structure_description,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"BrebotCrew.create_folder_structure({base_path})"
            )
            
            return f"Error creating folder structure: {str(e)}"
    
    def move_files_to_organized_structure(self, source_path: str, destination_base: str) -> str:
        """
        Move files to an organized structure using the File Organizer Agent.
        
        Args:
            source_path: Path to source files
            destination_base: Base path for organized destination
            
        Returns:
            str: Result of the file moving task
        """
        brebot_logger.log_crew_activity(
            crew_name="BrebotCrew",
            activity="move_files_to_organized_structure_started",
            details={
                "source_path": source_path,
                "destination_base": destination_base
            }
        )
        
        try:
            result = self.agents["file_organizer"].move_files_to_organized_structure(
                source_path=source_path,
                destination_base=destination_base
            )
            
            brebot_logger.log_crew_activity(
                crew_name="BrebotCrew",
                activity="move_files_to_organized_structure_completed",
                details={
                    "source_path": source_path,
                    "destination_base": destination_base,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"BrebotCrew.move_files_to_organized_structure({source_path}, {destination_base})"
            )
            
            return f"Error moving files: {str(e)}"
    
    def create_marketing_campaign(self, campaign_brief: str, target_audience: str, budget: str = None) -> str:
        """
        Create a marketing campaign using the Marketing Agent.
        
        Args:
            campaign_brief: Description of the campaign goals
            target_audience: Target audience description
            budget: Optional budget information
            
        Returns:
            str: Campaign strategy and recommendations
        """
        brebot_logger.log_crew_activity(
            crew_name="BrebotCrew",
            activity="create_marketing_campaign_started",
            details={
                "campaign_brief": campaign_brief,
                "target_audience": target_audience,
                "budget": budget
            }
        )
        
        try:
            result = self.agents["marketing"].create_marketing_campaign(
                campaign_brief=campaign_brief,
                target_audience=target_audience,
                budget=budget
            )
            
            brebot_logger.log_crew_activity(
                crew_name="BrebotCrew",
                activity="create_marketing_campaign_completed",
                details={
                    "campaign_brief": campaign_brief,
                    "target_audience": target_audience,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"BrebotCrew.create_marketing_campaign({campaign_brief})"
            )
            
            return f"Error creating marketing campaign: {str(e)}"
    
    def generate_marketing_content(self, content_type: str, topic: str, tone: str = "professional", length: str = "medium") -> str:
        """
        Generate marketing content using the Marketing Agent.
        
        Args:
            content_type: Type of content (blog post, social media, email, etc.)
            topic: Content topic
            tone: Content tone (professional, casual, friendly, etc.)
            length: Content length (short, medium, long)
            
        Returns:
            str: Generated content
        """
        brebot_logger.log_crew_activity(
            crew_name="BrebotCrew",
            activity="generate_marketing_content_started",
            details={
                "content_type": content_type,
                "topic": topic,
                "tone": tone,
                "length": length
            }
        )
        
        try:
            result = self.agents["marketing"].generate_content(
                content_type=content_type,
                topic=topic,
                tone=tone,
                length=length
            )
            
            brebot_logger.log_crew_activity(
                crew_name="BrebotCrew",
                activity="generate_marketing_content_completed",
                details={
                    "content_type": content_type,
                    "topic": topic,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"BrebotCrew.generate_marketing_content({content_type}, {topic})"
            )
            
            return f"Error generating marketing content: {str(e)}"
    
    def create_website_design(self, project_brief: str, target_audience: str, style_preferences: str = None) -> str:
        """
        Create a website design using the Web Design Agent.
        
        Args:
            project_brief: Description of the website project
            target_audience: Target audience description
            style_preferences: Optional style and design preferences
            
        Returns:
            str: Website design strategy and recommendations
        """
        brebot_logger.log_crew_activity(
            crew_name="BrebotCrew",
            activity="create_website_design_started",
            details={
                "project_brief": project_brief,
                "target_audience": target_audience,
                "style_preferences": style_preferences
            }
        )
        
        try:
            result = self.agents["web_design"].create_website_design(
                project_brief=project_brief,
                target_audience=target_audience,
                style_preferences=style_preferences
            )
            
            brebot_logger.log_crew_activity(
                crew_name="BrebotCrew",
                activity="create_website_design_completed",
                details={
                    "project_brief": project_brief,
                    "target_audience": target_audience,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"BrebotCrew.create_website_design({project_brief})"
            )
            
            return f"Error creating website design: {str(e)}"
    
    def optimize_user_experience(self, current_design: str, user_feedback: str = None, analytics_data: str = None) -> str:
        """
        Optimize user experience using the Web Design Agent.
        
        Args:
            current_design: Description of current design or website
            user_feedback: Optional user feedback and pain points
            analytics_data: Optional analytics data and metrics
            
        Returns:
            str: UX optimization recommendations
        """
        brebot_logger.log_crew_activity(
            crew_name="BrebotCrew",
            activity="optimize_user_experience_started",
            details={
                "current_design": current_design,
                "user_feedback": user_feedback,
                "analytics_data": analytics_data
            }
        )
        
        try:
            result = self.agents["web_design"].optimize_user_experience(
                current_design=current_design,
                user_feedback=user_feedback,
                analytics_data=analytics_data
            )
            
            brebot_logger.log_crew_activity(
                crew_name="BrebotCrew",
                activity="optimize_user_experience_completed",
                details={
                    "current_design": current_design,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"BrebotCrew.optimize_user_experience({current_design})"
            )
            
            return f"Error optimizing user experience: {str(e)}"
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get the status of all agents in the crew.
        
        Returns:
            dict: Status information for all agents
        """
        status = {
            "crew_name": "BrebotCrew",
            "timestamp": datetime.now().isoformat(),
            "llm_config": {
                "provider": self.llm_config["provider"],
                "model": self.llm_config["model"]
            },
            "agents": {}
        }
        
        for agent_name, agent in self.agents.items():
            status["agents"][agent_name] = {
                "name": agent_name,
                "type": type(agent).__name__,
                "tools_count": len(agent.tools) if hasattr(agent, 'tools') else 0,
                "status": "active"
            }
        
        return status
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the crew and all agents.
        
        Returns:
            dict: Health check results
        """
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        # Check LLM connectivity
        try:
            # Simple test to see if LLM is responsive
            test_response = self.llm.complete("Hello")
            health_status["checks"]["llm"] = {
                "status": "healthy",
                "response_length": len(str(test_response))
            }
        except Exception as e:
            health_status["checks"]["llm"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check embedding model
        try:
            test_embedding = self.embedding.get_text_embedding("test")
            health_status["checks"]["embedding"] = {
                "status": "healthy",
                "embedding_dimension": len(test_embedding)
            }
        except Exception as e:
            health_status["checks"]["embedding"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check agents
        for agent_name, agent in self.agents.items():
            try:
                # Basic agent health check
                health_status["checks"][f"agent_{agent_name}"] = {
                    "status": "healthy",
                    "tools_available": len(agent.tools) if hasattr(agent, 'tools') else 0
                }
            except Exception as e:
                health_status["checks"][f"agent_{agent_name}"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
        
        return health_status


# Export the crew class
__all__ = ["BrebotCrew"]
