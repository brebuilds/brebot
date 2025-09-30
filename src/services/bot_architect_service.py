"""Bot Architect service for assisting with bot design and creation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models.actions import BotAction
from utils import brebot_logger

from .bot_service import botService


def _slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-") or "bot"


@dataclass
class BotDesignSpec:
    goal: str
    description: Optional[str] = None
    name: Optional[str] = None
    primary_tasks: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    personality: Optional[str] = None
    auto_create: bool = False


class BotArchitectService:
    """Produce bot design recommendations and optionally create bots."""

    def __init__(self) -> None:
        self.department_keywords: Dict[str, List[str]] = {
            "Content Creation": ["content", "blog", "copy", "write", "script"],
            "Marketing": ["campaign", "marketing", "ad", "seo", "social"],
            "Data Management": ["data", "spreadsheet", "report", "catalog", "analysis"],
            "E-commerce": ["shopify", "store", "product", "inventory", "listing"],
            "Customer Service": ["support", "customer", "ticket", "faq"],
            "Automation": ["workflow", "automation", "integration", "api"],
        }

        self.tool_suggestions: Dict[str, List[str]] = {
            "file": ["ListFilesTool", "OrganizeFilesTool", "CreateFolderTool"],
            "web": ["WebAutomationTool", "WebScrapingTool", "WebWorkflowTool"],
            "api": ["APICallTool", "WorkflowSchedulerTool"],
            "marketing": ["CampaignDesignerTool", "ContentCalendarTool"],
            "content": ["DraftCreatorTool", "ToneAdjusterTool"],
            "data": ["SpreadsheetAnalyzerTool", "DashboardBuilderTool"],
            "voice": ["VoiceSynthesisTool"],
        }

    def _select_department(self, spec: BotDesignSpec) -> str:
        text = " ".join(
            filter(
                None,
                [
                    spec.goal,
                    spec.description,
                    " ".join(spec.primary_tasks),
                    " ".join(spec.integrations),
                ],
            )
        ).lower()

        for department, keywords in self.department_keywords.items():
            if any(keyword in text for keyword in keywords):
                return department
        return "Automation"

    def _select_type(self, spec: BotDesignSpec) -> str:
        text = " ".join(spec.primary_tasks).lower()
        if any(keyword in text for keyword in ["text", "write", "content", "copy"]):
            return "text_processing"
        if any(keyword in text for keyword in ["image", "design", "mockup"]):
            return "image_processing"
        if any(keyword in text for keyword in ["scrape", "browser", "web"]):
            return "web_scraping"
        if any(keyword in text for keyword in ["api", "integration", "workflow"]):
            return "api_integration"
        if any(keyword in text for keyword in ["file", "organize", "folder"]):
            return "file_management"
        if any(keyword in text for keyword in ["data", "report", "analysis", "spreadsheet"]):
            return "data_processing"
        return "text_processing"

    def _suggest_tools(self, spec: BotDesignSpec) -> List[str]:
        suggestions: List[str] = []
        corpus = " ".join(
            [
                spec.goal,
                spec.description or "",
                " ".join(spec.primary_tasks),
                " ".join(spec.integrations),
            ]
        ).lower()

        for keyword, tools in self.tool_suggestions.items():
            if keyword in corpus:
                for tool in tools:
                    if tool not in suggestions:
                        suggestions.append(tool)

        if not suggestions:
            suggestions.extend(["ListFilesTool", "APICallTool"])

        return suggestions[:8]

    def _build_checklist(self, spec: BotDesignSpec, bot_id: str) -> List[str]:
        checklist = [
            f"Confirm bot objective: {spec.goal}",
            f"Create operating guidelines for `{bot_id}`",
            "Review tool permissions and required connections",
        ]
        if spec.data_sources:
            checklist.append("Connect data sources: " + ", ".join(spec.data_sources))
        if spec.integrations:
            checklist.append("Verify integrations: " + ", ".join(spec.integrations))
        if spec.success_metrics:
            checklist.append("Track success metrics: " + ", ".join(spec.success_metrics))
        return checklist

    async def design_bot(self, spec: BotDesignSpec) -> Dict[str, Any]:
        brebot_logger.log_agent_action(
            "BotArchitectService",
            "design_requested",
            {"goal": spec.goal, "auto_create": spec.auto_create},
        )

        department = self._select_department(spec)
        bot_type = self._select_type(spec)
        suggested_tools = self._suggest_tools(spec)
        bot_name = spec.name or spec.goal
        bot_id = _slugify(bot_name or spec.goal)

        responsibilities = spec.primary_tasks or [
            f"Handle tasks related to {spec.goal.lower()}"
        ]

        persona = spec.personality or "Supportive and proactive"

        recommendation = {
            "bot_id": bot_id,
            "name": bot_name,
            "department": department,
            "bot_type": bot_type,
            "description": spec.description or spec.goal,
            "responsibilities": responsibilities,
            "suggested_tools": suggested_tools,
            "data_sources": spec.data_sources,
            "integrations": spec.integrations,
            "success_metrics": spec.success_metrics,
            "persona": persona,
        }

        checklist = self._build_checklist(spec, bot_id)

        result: Dict[str, Any] = {
            "status": "draft",
            "recommendation": recommendation,
            "checklist": checklist,
        }

        if spec.auto_create:
            action = BotAction(
                type="bot.create",
                id=bot_id,
                name=bot_name,
                role=spec.goal,
                responsibilities=responsibilities,
                provider=None,
            )
            create_result = await botService.create(action)
            result["status"] = create_result.get("status", "success")
            result["created_bot"] = create_result.get("bot")

        return result


botArchitectService = BotArchitectService()

__all__ = ["botArchitectService", "BotDesignSpec", "BotArchitectService"]
