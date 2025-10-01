import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.actions import Action
from src.services import taskService, noteService, memoryService, inboxService
from src.services import meetingService, botService, creativeService, systemService
from src.services import businessService, fileService, financeService, interactionService


async def route_action(action: Action):
    """Route Brebot actions to the correct service layer."""

    # ----------------- Tasks -----------------
    if action.root.type == "task.create":
        return await taskService.create(action.root)
    elif action.root.type == "task.update":
        return await taskService.update(action.root)
    elif action.root.type == "task.delete":
        return await taskService.delete(action.root.id)
    elif action.root.type == "task.list":
        return await taskService.list()

    # ----------------- Notes -----------------
    elif action.root.type == "note.create":
        return await noteService.create(action.root)
    elif action.root.type == "note.update":
        return await noteService.update(action.root)
    elif action.root.type == "note.delete":
        return await noteService.delete(action.root.id)
    elif action.root.type == "note.list":
        return await noteService.list()

    # ----------------- Memory -----------------
    elif action.root.type == "memory.add":
        return await memoryService.add(action.root)
    elif action.root.type == "memory.update":
        return await memoryService.update(action.root)
    elif action.root.type == "memory.delete":
        return await memoryService.delete(action.root.id)
    elif action.root.type == "memory.search":
        return await memoryService.search(
            query=action.root.query,
            tags=action.root.tags,
            domain=getattr(action.root, "domain", None),
            project=getattr(action.root, "project", None),
            source_type=getattr(action.root, "source_type", None),
        )

    # ----------------- Inbox -----------------
    elif action.root.type == "inbox.notify":
        return await inboxService.notify(action.root)
    elif action.root.type == "inbox.mark_read":
        return await inboxService.mark_read(action.root.id)
    elif action.root.type == "inbox.mark_unread":
        return await inboxService.mark_unread(action.root.id)
    elif action.root.type == "inbox.pin":
        return await inboxService.pin(action.root.id)

    # ----------------- Meetings -----------------
    elif action.root.type == "meeting.create":
        return await meetingService.create(action.root)
    elif action.root.type == "meeting.start":
        return await meetingService.start(action.root)
    elif action.root.type == "meeting.summarize":
        return await meetingService.summarize(action.root.id)
    elif action.root.type == "meeting.cancel":
        return await meetingService.cancel(action.root.id)

    # ----------------- Bots -----------------
    elif action.root.type == "bot.create":
        return await botService.create(action.root)
    elif action.root.type == "bot.update":
        return await botService.update(action.root)
    elif action.root.type == "bot.delete":
        return await botService.delete(action.root.id)
    elif action.root.type == "bot.train":
        return await botService.train(action.root)
    elif action.root.type == "bot.assign_task":
        return await botService.assign_task(action.root)
    elif action.root.type == "bot.list":
        return await botService.list()

    # ----------------- Creative -----------------
    elif action.root.type == "idea.generate":
        return await creativeService.generate_ideas(action.root)
    elif action.root.type == "art.generate":
        return await creativeService.generate_art(action.root)
    elif action.root.type == "research.summarize":
        return await creativeService.summarize_research(action.root)
    elif action.root.type == "research.find":
        return await creativeService.find_research(action.root.query)
    elif action.root.type == "trend.check":
        return await creativeService.check_trends()
    elif action.root.type == "market.scan":
        return await creativeService.scan_marketplaces()
    elif action.root.type == "content.generate":
        return await creativeService.generate_content(action.root)
    elif action.root.type == "content.bundle":
        return await creativeService.bundle_content(action.root)
    elif action.root.type == "doc.generate":
        return await creativeService.generate_doc(action.root)

    # ----------------- System -----------------
    elif action.root.type == "connection.enable":
        return await systemService.enable_connection(action.root.service)
    elif action.root.type == "connection.disable":
        return await systemService.disable_connection(action.root.service)
    elif action.root.type == "connection.health_check":
        return await systemService.health_check(action.root.service)
    elif action.root.type == "connection.toggle_ingestion":
        return await systemService.toggle_ingestion(action.root.service)
    elif action.root.type == "calendar.add_event":
        return await systemService.add_calendar_event(action.root)
    elif action.root.type == "calendar.update_event":
        return await systemService.update_calendar_event(action.root)
    elif action.root.type == "calendar.delete_event":
        return await systemService.delete_calendar_event(action.root.event_id)
    elif action.root.type == "calendar.check":
        return await systemService.check_calendar(action.root.query)
    elif action.root.type == "alert.create":
        return await systemService.create_alert(action.root)
    elif action.root.type == "alert.resolve":
        return await systemService.resolve_alert(action.root.id)
    elif action.root.type == "subscription.cancel":
        return await systemService.cancel_subscription(action.root)
    elif action.root.type == "system.diagnose":
        return await systemService.diagnose(action.root)

    # ----------------- Business -----------------
    elif action.root.type == "invoice.generate":
        return await businessService.generate_invoice(action.root)
    elif action.root.type == "brochure.generate":
        return await businessService.generate_brochure(action.root)
    elif action.root.type == "guide.generate":
        return await businessService.generate_guide(action.root)
    elif action.root.type == "backlog.generate":
        return await businessService.generate_backlog(action.root)

    # ----------------- Files -----------------
    elif action.root.type == "files.search":
        return await fileService.search(action.root.query)
    elif action.root.type == "files.organize":
        return await fileService.organize(action.root.folder)

    # ----------------- Finance -----------------
    elif action.root.type == "finance.plan":
        return await financeService.make_plan(action.root)
    elif action.root.type == "gift.generate":
        return await financeService.generate_gifts(action.root.family_members)

    # ----------------- Interaction -----------------
    elif action.root.type == "voice.transcribe":
        return await interactionService.transcribe(action.root)
    elif action.root.type == "voice.reply":
        return await interactionService.reply(action.root)
    elif action.root.type == "voice.assign":
        return await interactionService.assign(action.root)
    elif action.root.type == "tool.create":
        return await interactionService.create_tool(action.root)

    # ----------------- Projects -----------------
    elif action.root.type == "project.assist":
        return await systemService.assist_project(action.root)
    elif action.root.type == "project.list":
        return await systemService.list_projects()

    # ----------------- Default -----------------
    elif action.root.type == "none":
        return {"message": "No action taken."}

    else:
        return {"error": f"Unknown action type: {action.root.type}"}
