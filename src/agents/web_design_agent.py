"""
Web Design Agent for Brebot.
An AI agent specialized in web design, UI/UX, and frontend development.
"""

from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

from config import get_llm_config, get_embedding_config, settings
from utils import brebot_logger


class WebDesignAgent:
    """Web Design Agent that can handle web design and development tasks."""
    
    def __init__(self, llm_config: dict = None, embedding_config: dict = None):
        """
        Initialize the Web Design Agent.
        
        Args:
            llm_config: LLM configuration dictionary
            embedding_config: Embedding configuration dictionary
        """
        self.llm_config = llm_config or get_llm_config(settings)
        self.embedding_config = embedding_config or get_embedding_config(settings)
        
        # Initialize LLM and embedding models
        self.llm = self._setup_llm()
        self.embedding = self._setup_embedding()
        
        # Create the agent
        self.agent = self._create_agent()
        
        brebot_logger.log_agent_action(
            agent_name="WebDesignAgent",
            action="initialized",
            details={
                "llm_provider": self.llm_config["provider"],
                "llm_model": self.llm_config["model"]
            }
        )
    
    def _setup_llm(self):
        """Set up the LLM based on configuration."""
        if self.llm_config["provider"] == "ollama":
            return Ollama(
                model=self.llm_config["model"],
                base_url=self.llm_config["base_url"],
                temperature=0.2,  # Lower temperature for more consistent design decisions
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
    
    def _create_agent(self) -> Agent:
        """Create the Web Design Agent."""
        return Agent(
            role="Web Design & UX Specialist",
            goal="""Create beautiful, functional, and user-friendly web designs that 
            provide exceptional user experiences. Focus on modern design principles, 
            accessibility, and responsive design that works across all devices.""",
            
            backstory="""You are an expert web designer and UX specialist with over 8 years 
            of experience in creating stunning websites and user interfaces. You have a deep 
            understanding of design principles, user psychology, and modern web technologies. 
            You excel at creating wireframes, mockups, and prototypes that balance aesthetics 
            with functionality. You're known for your attention to detail, creative problem-solving, 
            and ability to translate client requirements into beautiful, user-friendly designs 
            that drive engagement and conversions.""",
            
            verbose=settings.agent_verbose,
            allow_delegation=False,
            tools=[],  # We'll add design-specific tools later
            llm=self.llm,
            max_iter=settings.agent_max_iter,
            memory=settings.agent_memory,
            max_execution_time=300,
            
            system_message="""You are a Web Design & UX Specialist. Your expertise includes:

1. **UI/UX Design**: Create intuitive and beautiful user interfaces
2. **Responsive Design**: Design for all devices and screen sizes
3. **Wireframing**: Create detailed wireframes and prototypes
4. **Design Systems**: Develop consistent design systems and style guides
5. **Accessibility**: Ensure designs are accessible to all users
6. **Frontend Development**: HTML, CSS, JavaScript, and modern frameworks
7. **Performance**: Optimize designs for speed and performance
8. **User Research**: Conduct user research and usability testing

When given a design task:
- Understand the user needs and business goals
- Create user-centered designs
- Follow modern design principles and best practices
- Ensure accessibility and responsive design
- Provide detailed specifications and guidelines
- Consider performance and technical feasibility

Always prioritize user experience and accessibility."""
        )
    
    def create_website_design(self, project_brief: str, target_audience: str, style_preferences: str = None) -> str:
        """
        Create a comprehensive website design plan.
        
        Args:
            project_brief: Description of the website project
            target_audience: Target audience description
            style_preferences: Optional style and design preferences
            
        Returns:
            str: Website design strategy and recommendations
        """
        brebot_logger.log_agent_action(
            agent_name="WebDesignAgent",
            action="create_website_design",
            details={
                "project_brief": project_brief,
                "target_audience": target_audience,
                "style_preferences": style_preferences
            }
        )
        
        task = Task(
            description=f"""
            Create a comprehensive website design plan based on the following brief:
            
            Project Brief: {project_brief}
            Target Audience: {target_audience}
            Style Preferences: {style_preferences or 'Modern and professional'}
            
            Please develop:
            1. User experience strategy and user journey mapping
            2. Information architecture and site structure
            3. Wireframe recommendations and layout concepts
            4. Visual design direction and style guide
            5. Responsive design strategy
            6. Accessibility considerations
            7. Performance optimization recommendations
            8. Technical implementation guidelines
            
            Make sure to:
            - Focus on user-centered design
            - Consider the target audience's needs
            - Include modern design trends and best practices
            - Ensure accessibility compliance
            - Provide specific, actionable recommendations
            - Include technical considerations
            """,
            expected_output="""A comprehensive website design plan including:
            - Executive summary and design objectives
            - User experience strategy
            - Information architecture
            - Wireframe concepts and layouts
            - Visual design direction
            - Responsive design strategy
            - Accessibility guidelines
            - Performance recommendations
            - Technical implementation plan
            - Timeline and deliverables""",
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
                crew_name="WebDesignCrew",
                activity="create_website_design_completed",
                details={
                    "project_brief": project_brief,
                    "target_audience": target_audience,
                    "success": True
                }
            )
            
            return str(result)
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"WebDesignAgent.create_website_design({project_brief})"
            )
            
            return f"Error creating website design: {str(e)}"
    
    def create_ui_components(self, component_type: str, purpose: str, style_guide: str = None) -> str:
        """
        Create UI component designs and specifications.
        
        Args:
            component_type: Type of UI component (button, form, card, etc.)
            purpose: Purpose and functionality of the component
            style_guide: Optional style guide or design system
            
        Returns:
            str: UI component design and specifications
        """
        brebot_logger.log_agent_action(
            agent_name="WebDesignAgent",
            action="create_ui_components",
            details={
                "component_type": component_type,
                "purpose": purpose,
                "style_guide": style_guide
            }
        )
        
        task = Task(
            description=f"""
            Design a {component_type} component with the following specifications:
            
            Component Type: {component_type}
            Purpose: {purpose}
            Style Guide: {style_guide or 'Modern and clean design'}
            
            Please create:
            1. Component design and visual specifications
            2. Interactive states and behaviors
            3. Responsive design considerations
            4. Accessibility features and requirements
            5. Technical implementation guidelines
            6. Code examples and best practices
            7. Testing and validation criteria
            
            Make sure the component is:
            - User-friendly and intuitive
            - Accessible to all users
            - Responsive across devices
            - Consistent with design system
            - Technically feasible
            - Well-documented
            """,
            expected_output=f"""Comprehensive {component_type} component design including:
            - Visual design specifications
            - Interactive states and behaviors
            - Responsive design guidelines
            - Accessibility requirements
            - Technical implementation details
            - Code examples and snippets
            - Testing and validation criteria
            - Usage guidelines and best practices""",
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
                crew_name="WebDesignCrew",
                activity="create_ui_components_completed",
                details={
                    "component_type": component_type,
                    "purpose": purpose,
                    "success": True
                }
            )
            
            return str(result)
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"WebDesignAgent.create_ui_components({component_type}, {purpose})"
            )
            
            return f"Error creating UI components: {str(e)}"
    
    def optimize_user_experience(self, current_design: str, user_feedback: str = None, analytics_data: str = None) -> str:
        """
        Analyze and optimize user experience.
        
        Args:
            current_design: Description of current design or website
            user_feedback: Optional user feedback and pain points
            analytics_data: Optional analytics data and metrics
            
        Returns:
            str: UX optimization recommendations
        """
        brebot_logger.log_agent_action(
            agent_name="WebDesignAgent",
            action="optimize_user_experience",
            details={
                "current_design": current_design,
                "user_feedback": user_feedback,
                "analytics_data": analytics_data
            }
        )
        
        task = Task(
            description=f"""
            Analyze and optimize the user experience for the following design:
            
            Current Design: {current_design}
            User Feedback: {user_feedback or 'No specific feedback provided'}
            Analytics Data: {analytics_data or 'No analytics data provided'}
            
            Please analyze:
            1. Current user experience and pain points
            2. User journey and conversion funnel analysis
            3. Usability issues and accessibility concerns
            4. Performance and loading time optimization
            5. Mobile responsiveness and cross-device experience
            6. Content organization and information architecture
            7. Call-to-action placement and effectiveness
            8. Navigation and user flow improvements
            
            Provide specific recommendations for:
            - Design improvements and changes
            - User interface enhancements
            - Content optimization
            - Technical performance improvements
            - Accessibility enhancements
            - Mobile experience improvements
            """,
            expected_output="""Comprehensive UX optimization report including:
            - Current state analysis
            - Identified pain points and issues
            - User journey optimization recommendations
            - Design improvement suggestions
            - Technical performance recommendations
            - Accessibility enhancement plan
            - Mobile experience improvements
            - Implementation priority and timeline
            - Expected impact and metrics""",
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
                crew_name="WebDesignCrew",
                activity="optimize_user_experience_completed",
                details={
                    "current_design": current_design,
                    "success": True
                }
            )
            
            return str(result)
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"WebDesignAgent.optimize_user_experience({current_design})"
            )
            
            return f"Error optimizing user experience: {str(e)}"


# Export the agent class
__all__ = ["WebDesignAgent"]
