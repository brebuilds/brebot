"""
Marketing Agent for Brebot.
An AI agent specialized in marketing tasks and campaign management.
"""

from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

from config import get_llm_config, get_embedding_config, settings
from utils import brebot_logger


class MarketingAgent:
    """Marketing Agent that can handle marketing tasks and campaigns."""
    
    def __init__(self, llm_config: dict = None, embedding_config: dict = None):
        """
        Initialize the Marketing Agent.
        
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
            agent_name="MarketingAgent",
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
                temperature=0.3,  # Slightly higher for creative marketing content
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
        """Create the Marketing Agent."""
        return Agent(
            role="Marketing Strategy Specialist",
            goal="""Create compelling marketing campaigns, develop brand strategies, 
            and generate engaging content that drives customer engagement and sales. 
            Focus on data-driven marketing decisions and creative content creation.""",
            
            backstory="""You are an expert marketing strategist with over 10 years of experience 
            in digital marketing, brand development, and campaign management. You have a deep 
            understanding of consumer psychology, market trends, and digital marketing channels. 
            You excel at creating compelling content, developing marketing strategies, and 
            analyzing campaign performance. You're known for your creative approach to marketing 
            challenges and your ability to translate complex marketing concepts into actionable 
            strategies that deliver results.""",
            
            verbose=settings.agent_verbose,
            allow_delegation=False,
            tools=[],  # We'll add marketing-specific tools later
            llm=self.llm,
            max_iter=settings.agent_max_iter,
            memory=settings.agent_memory,
            max_execution_time=300,
            
            system_message="""You are a Marketing Strategy Specialist. Your expertise includes:

1. **Campaign Development**: Create comprehensive marketing campaigns
2. **Content Creation**: Generate engaging marketing copy and content
3. **Brand Strategy**: Develop brand positioning and messaging
4. **Market Analysis**: Analyze market trends and competitor strategies
5. **Social Media Marketing**: Create social media strategies and content
6. **Email Marketing**: Design email campaigns and sequences
7. **SEO & SEM**: Develop search marketing strategies
8. **Analytics**: Interpret marketing data and optimize campaigns

When given a marketing task:
- Research the target audience and market
- Develop a comprehensive strategy
- Create compelling content and messaging
- Provide actionable recommendations
- Include metrics for measuring success

Always focus on ROI and measurable results."""
        )
    
    def create_marketing_campaign(self, campaign_brief: str, target_audience: str, budget: str = None) -> str:
        """
        Create a comprehensive marketing campaign.
        
        Args:
            campaign_brief: Description of the campaign goals
            target_audience: Target audience description
            budget: Optional budget information
            
        Returns:
            str: Campaign strategy and recommendations
        """
        brebot_logger.log_agent_action(
            agent_name="MarketingAgent",
            action="create_marketing_campaign",
            details={
                "campaign_brief": campaign_brief,
                "target_audience": target_audience,
                "budget": budget
            }
        )
        
        task = Task(
            description=f"""
            Create a comprehensive marketing campaign based on the following brief:
            
            Campaign Brief: {campaign_brief}
            Target Audience: {target_audience}
            Budget: {budget or 'Not specified'}
            
            Please develop:
            1. Campaign objectives and KPIs
            2. Target audience analysis
            3. Marketing channels and tactics
            4. Content strategy and messaging
            5. Timeline and milestones
            6. Budget allocation recommendations
            7. Success metrics and measurement plan
            
            Make sure to:
            - Align with business objectives
            - Consider the target audience's preferences
            - Include both digital and traditional channels
            - Provide specific, actionable recommendations
            - Include realistic timelines and budgets
            """,
            expected_output="""A comprehensive marketing campaign plan including:
            - Executive summary
            - Campaign objectives and KPIs
            - Target audience analysis
            - Marketing channel strategy
            - Content and messaging framework
            - Implementation timeline
            - Budget recommendations
            - Success metrics and measurement plan
            - Risk assessment and mitigation strategies""",
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
                crew_name="MarketingCrew",
                activity="create_marketing_campaign_completed",
                details={
                    "campaign_brief": campaign_brief,
                    "target_audience": target_audience,
                    "success": True
                }
            )
            
            return str(result)
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"MarketingAgent.create_marketing_campaign({campaign_brief})"
            )
            
            return f"Error creating marketing campaign: {str(e)}"
    
    def generate_content(self, content_type: str, topic: str, tone: str = "professional", length: str = "medium") -> str:
        """
        Generate marketing content.
        
        Args:
            content_type: Type of content (blog post, social media, email, etc.)
            topic: Content topic
            tone: Content tone (professional, casual, friendly, etc.)
            length: Content length (short, medium, long)
            
        Returns:
            str: Generated content
        """
        brebot_logger.log_agent_action(
            agent_name="MarketingAgent",
            action="generate_content",
            details={
                "content_type": content_type,
                "topic": topic,
                "tone": tone,
                "length": length
            }
        )
        
        task = Task(
            description=f"""
            Generate {content_type} content with the following specifications:
            
            Topic: {topic}
            Tone: {tone}
            Length: {length}
            
            Please create engaging, high-quality content that:
            - Captures the reader's attention
            - Provides value to the target audience
            - Aligns with the specified tone
            - Is optimized for the content type
            - Includes a clear call-to-action
            - Is SEO-friendly (if applicable)
            
            Make sure the content is:
            - Original and creative
            - Well-structured and easy to read
            - Engaging and compelling
            - Appropriate for the target audience
            """,
            expected_output=f"""High-quality {content_type} content including:
            - Compelling headline/title
            - Well-structured body content
            - Clear call-to-action
            - SEO optimization (if applicable)
            - Engagement elements
            - Brand-appropriate messaging""",
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
                crew_name="MarketingCrew",
                activity="generate_content_completed",
                details={
                    "content_type": content_type,
                    "topic": topic,
                    "success": True
                }
            )
            
            return str(result)
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"MarketingAgent.generate_content({content_type}, {topic})"
            )
            
            return f"Error generating content: {str(e)}"
    
    def analyze_competitors(self, industry: str, company_name: str = None) -> str:
        """
        Analyze competitors and market positioning.
        
        Args:
            industry: Industry to analyze
            company_name: Optional specific company to focus on
            
        Returns:
            str: Competitive analysis report
        """
        brebot_logger.log_agent_action(
            agent_name="MarketingAgent",
            action="analyze_competitors",
            details={
                "industry": industry,
                "company_name": company_name
            }
        )
        
        task = Task(
            description=f"""
            Conduct a comprehensive competitive analysis for the {industry} industry.
            
            Focus Company: {company_name or 'General industry analysis'}
            
            Please analyze:
            1. Key competitors and their market position
            2. Competitive advantages and disadvantages
            3. Pricing strategies and positioning
            4. Marketing channels and tactics used
            5. Content strategies and messaging
            6. Customer acquisition approaches
            7. Market gaps and opportunities
            8. Recommendations for competitive advantage
            
            Provide actionable insights that can inform:
            - Marketing strategy development
            - Product positioning
            - Pricing decisions
            - Content creation
            - Channel selection
            """,
            expected_output="""A comprehensive competitive analysis including:
            - Executive summary
            - Competitor landscape overview
            - Detailed competitor profiles
            - Market positioning analysis
            - Competitive advantages assessment
            - Market opportunities identification
            - Strategic recommendations
            - Action plan for competitive advantage""",
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
                crew_name="MarketingCrew",
                activity="analyze_competitors_completed",
                details={
                    "industry": industry,
                    "company_name": company_name,
                    "success": True
                }
            )
            
            return str(result)
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context=f"MarketingAgent.analyze_competitors({industry})"
            )
            
            return f"Error analyzing competitors: {str(e)}"


# Export the agent class
__all__ = ["MarketingAgent"]
