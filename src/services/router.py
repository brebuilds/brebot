from models.actions import Action
from services import taskService, noteService, memoryService, inboxService
from services import meetingService, botService, creativeService, systemService
from services import businessService, fileService, financeService, interactionService


async def route_action(action: Action):
    """Route Brebot actions to the correct service layer."""

    # ----------------- Tasks -----------------
    if action.type == "task.create":
        return await taskService.create(action)
    elif action.type == "task.update":
        return await taskService.update(action)
    elif action.type == "task.delete":
        return await taskService.delete(action.id)
    elif action.type == "task.list":
        return await taskService.list()

    # ----------------- Notes -----------------
    elif action.type == "note.create":
        return await noteService.create(action)
    elif action.type == "note.update":
        return await noteService.update(action)
    elif action.type == "note.delete":
        return await noteService.delete(action.id)
    elif action.type == "note.list":
        return await noteService.list()

    # ----------------- Memory -----------------
    elif action.type == "memory.add":
        return await memoryService.add(action)
    elif action.type == "memory.update":
        return await memoryService.update(action)
    elif action.type == "memory.delete":
        return await memoryService.delete(action.id)
    elif action.type == "memory.search":
        return await memoryService.search(
            query=action.query,
            tags=action.tags,
            domain=action.domain,
            project=action.project,
            source_type=action.source_type,
        )

    # ----------------- Inbox -----------------
    elif action.type == "inbox.notify":
        return await inboxService.notify(action)
    elif action.type == "inbox.mark_read":
        return await inboxService.mark_read(action.id)
    elif action.type == "inbox.mark_unread":
        return await inboxService.mark_unread(action.id)
    elif action.type == "inbox.pin":
        return await inboxService.pin(action.id)

    # ----------------- Meetings -----------------
    elif action.type == "meeting.create":
        return await meetingService.create(action)
    elif action.type == "meeting.start":
        return await meetingService.start(action)
    elif action.type == "meeting.summarize":
        return await meetingService.summarize(action.id)
    elif action.type == "meeting.cancel":
        return await meetingService.cancel(action.id)

    # ----------------- Bots -----------------
    elif action.type == "bot.create":
        return await botService.create(action)
    elif action.type == "bot.update":
        return await botService.update(action)
    elif action.type == "bot.delete":
        return await botService.delete(action.id)
    elif action.type == "bot.train":
        return await botService.train(action)
    elif action.type == "bot.assign_task":
        return await botService.assign_task(action)
    elif action.type == "bot.list":
        return await botService.list()

    # ----------------- Creative -----------------
    elif action.type == "idea.generate":
        return await creativeService.generate_ideas(action)
    elif action.type == "art.generate":
        return await creativeService.generate_art(action)
    elif action.type == "research.summarize":
        return await creativeService.summarize_research(action)
    elif action.type == "research.find":
        return await creativeService.find_research(action.query)
    elif action.type == "trend.check":
        return await creativeService.check_trends()
    elif action.type == "market.scan":
        return await creativeService.scan_marketplaces()
    elif action.type == "content.generate":
        return await creativeService.generate_content(action)
    elif action.type == "content.bundle":
        return await creativeService.bundle_content(action)
    elif action.type == "doc.generate":
        return await creativeService.generate_doc(action)

    # ----------------- System -----------------
    elif action.type == "connection.enable":
        return await systemService.enable_connection(action.service)
    elif action.type == "connection.disable":
        return await systemService.disable_connection(action.service)
    elif action.type == "connection.health_check":
        return await systemService.health_check(action.service)
    elif action.type == "connection.toggle_ingestion":
        return await systemService.toggle_ingestion(action.service)
    elif action.type == "calendar.add_event":
        return await systemService.add_calendar_event(action)
    elif action.type == "calendar.update_event":
        return await systemService.update_calendar_event(action)
    elif action.type == "calendar.delete_event":
        return await systemService.delete_calendar_event(action.event_id)
    elif action.type == "calendar.check":
        return await systemService.check_calendar(action.query)
    elif action.type == "alert.create":
        return await systemService.create_alert(action)
    elif action.type == "alert.resolve":
        return await systemService.resolve_alert(action.id)
    elif action.type == "subscription.cancel":
        return await systemService.cancel_subscription(action)
    elif action.type == "system.diagnose":
        return await systemService.diagnose(action)

    # ----------------- Business -----------------
    elif action.type == "invoice.generate":
        return await businessService.generate_invoice(action)
    elif action.type == "brochure.generate":
        return await businessService.generate_brochure(action)
    elif action.type == "guide.generate":
        return await businessService.generate_guide(action)
    elif action.type == "backlog.generate":
        return await businessService.generate_backlog(action)

    # ----------------- Files -----------------
    elif action.type == "files.search":
        return await fileService.search(action.query)
    elif action.type == "files.organize":
        return await fileService.organize(action.folder)

    # ----------------- Finance -----------------
    elif action.type == "finance.plan":
        return await financeService.make_plan(action)
    elif action.type == "gift.generate":
        return await financeService.generate_gifts(action.family_members)

    # ----------------- Interaction -----------------
    elif action.type == "voice.transcribe":
        return await interactionService.transcribe(action)
    elif action.type == "voice.reply":
        return await interactionService.reply(action)
    elif action.type == "voice.assign":
        return await interactionService.assign(action)
    elif action.type == "tool.create":
        return await interactionService.create_tool(action)

    # ----------------- Projects -----------------
    elif action.type == "project.assist":
        return await systemService.assist_project(action)
    elif action.type == "project.list":
        return await systemService.list_projects()

    # ----------------- Default -----------------
    elif action.type == "none":
        return {"message": "No action taken."}

    else:
        return {"error": f"Unknown action type: {action.type}"}
