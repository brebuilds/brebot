# Brebot System Prompts Guide

This guide explains how to use and customize the centralized system prompts for your Brebot AI assistant.

## 🎯 **Overview**

The system prompts are now centralized in `src/config/system_prompts.py`, making it easy to manage and customize all AI interactions across your Brebot system.

## 📁 **File Structure**

```
src/config/
├── system_prompts.py    # Centralized prompts
├── settings.py          # Configuration settings
└── __init__.py          # Package exports
```

## 🚀 **Quick Usage**

### **Import and Use**
```python
from config.system_prompts import get_chat_prompt, get_voice_prompt

# Get chat prompt
chat_prompt = get_chat_prompt()

# Get voice prompt  
voice_prompt = get_voice_prompt()
```

### **Available Prompts**

#### **Core Prompts**
- `get_chat_prompt()` - Your custom Brebot personality for chat
- `get_voice_prompt()` - Voice communication prompt
- `get_agent_prompt(agent_type)` - Agent-specific prompts

#### **System Prompts**
- `get_system_prompt(system_type)` - System management prompts
- `get_tool_prompt(tool_type)` - Tool-specific prompts
- `get_response_template(template_type)` - Response templates

## 🎨 **Your Custom Chat Prompt**

Your specific Brebot personality is now stored as `CHAT_INTERFACE` in the system prompts file. It includes:

- **Personality**: Conversational, funny, and a little chaotic
- **Context**: Bre's ADHD, multiple brands, and creative workflow
- **Output Rules**: Two-part responses (chat_reply + action)
- **Examples**: Real examples of how to respond to different inputs

### **Key Features**
- **Brand Awareness**: Knows about Mostly Coastly, Funky Legs, Threads for Heads, etc.
- **ADHD Support**: Breaks things into steps, provides encouragement
- **Action Routing**: Converts conversations into structured actions
- **Fun Tone**: Uses humor and puns while staying productive

## 🔧 **Customization**

### **Modifying Your Chat Prompt**
Edit the `CHAT_INTERFACE` constant in `src/config/system_prompts.py`:

```python
CHAT_INTERFACE = """Your updated prompt here..."""
```

### **Adding New Prompts**
Add new prompt constants to the `SystemPrompts` class:

```python
class SystemPrompts:
    # ... existing prompts ...
    
    NEW_PROMPT = """Your new prompt here..."""
    
    @classmethod
    def get_new_prompt(cls) -> str:
        return cls.NEW_PROMPT
```

### **Using Prompts in Code**
```python
# In your agents or services
from config.system_prompts import SystemPrompts

# Get a specific prompt
prompt = SystemPrompts.get_prompt("chat_interface")

# Get with formatting
prompt = SystemPrompts.get_prompt("success_response", 
                                 operation_summary="File organized",
                                 next_steps="Check the organized folder")
```

## 📋 **Available Prompt Types**

### **Agent Prompts**
- `file_organizer` - File management and organization
- `marketing` - Marketing content and campaigns  
- `web_design` - Web design and UI/UX
- `web_automation` - Browser automation and scraping

### **System Prompts**
- `connection_management` - External service connections
- `task_management` - Task and workflow management
- `memory_management` - Knowledge and memory system
- `n8n_integration` - N8N workflow automation
- `error_handling` - Error handling and recovery
- `security_privacy` - Security and privacy guidelines

### **Tool Prompts**
- `web_automation` - Web automation best practices
- `file_operation` - File operation safety guidelines

### **Response Templates**
- `success` - Success response template
- `error` - Error response template
- `progress` - Progress update template
- `context_aware` - Context-aware response template

## 🎭 **Brand Context**

The system includes brand-specific context for Bre's multiple brands:

- **Mostly Coastly**: Coastal, beachy, relaxed vibes
- **Funky Legs**: Playful, colorful, fun designs
- **Threads for Heads**: Headwear, accessories, trendy
- **Design & Chill**: Design services, professional yet approachable
- **LocAI**: AI tools, tech-forward, innovative
- **AiDHD**: ADHD-friendly tools, organized, supportive

## 🧠 **ADHD Support**

Special prompts for supporting Bre's ADHD needs:

- Break complex tasks into small steps
- Provide clear, actionable instructions
- Use visual cues and progress indicators
- Offer multiple approaches to goals
- Provide gentle reminders and encouragement
- Celebrate small wins and progress

## 🔄 **Integration Points**

### **Voice Service**
The voice service automatically uses your custom prompt:
```python
# In src/services/voice_service.py
self.system_prompt = get_voice_prompt()
```

### **Web App**
The chat interface uses your custom prompt:
```python
# In src/web/app.py
system_prompt = get_chat_prompt()
```

### **Agents**
Individual agents can use their specific prompts:
```python
# In your agent code
from config.system_prompts import get_agent_prompt

agent_prompt = get_agent_prompt("marketing")
```

## 🛠️ **Advanced Usage**

### **Dynamic Prompt Selection**
```python
from config.system_prompts import SystemPrompts

# Get all available prompts
all_prompts = SystemPrompts.get_all_prompts()

# Get prompt with custom formatting
prompt = SystemPrompts.get_response_template(
    "success",
    operation_summary="Files organized successfully",
    additional_details="Created 5 new folders",
    next_steps="Review the organized structure"
)
```

### **Custom Prompt Classes**
```python
class CustomPrompts(SystemPrompts):
    CUSTOM_PROMPT = """Your custom prompt..."""
    
    @classmethod
    def get_custom_prompt(cls) -> str:
        return cls.CUSTOM_PROMPT
```

## 📝 **Best Practices**

1. **Keep Prompts Focused**: Each prompt should have a clear, specific purpose
2. **Use Consistent Tone**: Maintain Bre's personality across all prompts
3. **Include Examples**: Provide clear examples of expected outputs
4. **Test Changes**: Test prompt changes with real interactions
5. **Version Control**: Track prompt changes in your git history
6. **Documentation**: Document any custom prompts you add

## 🚨 **Important Notes**

- **Backup**: Always backup your prompts before making changes
- **Testing**: Test prompt changes in a development environment first
- **Consistency**: Ensure all prompts align with Bre's personality and needs
- **Performance**: Large prompts may impact response times
- **Context**: Consider the context where each prompt will be used

## 🎉 **What This Enables**

With centralized system prompts, you can now:

- **Easily customize** Brebot's personality and behavior
- **Maintain consistency** across all AI interactions
- **Quickly update** prompts without code changes
- **Test different approaches** by swapping prompts
- **Scale prompt management** as your system grows
- **Version control** your AI personality and behavior

Your Brebot system now has a **centralized, manageable approach** to AI prompts that makes it easy to maintain Bre's unique personality while scaling your automation capabilities!

---

**Ready to customize?** Edit `src/config/system_prompts.py` to fine-tune Brebot's personality and behavior! 🎨🤖
