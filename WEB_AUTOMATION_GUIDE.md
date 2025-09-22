# Brebot Web Automation & Browser Control Guide

This guide covers Brebot's autonomous web capabilities, browser automation, and n8n integration for advanced workflow automation.

## 🌐 **Web Automation Capabilities**

### **Browser Automation**
Brebot can now autonomously control web browsers to perform complex tasks:

- **Navigation**: Navigate to any URL
- **Form Filling**: Automatically fill web forms
- **Clicking**: Click buttons, links, and interactive elements
- **Scraping**: Extract data from web pages
- **Screenshots**: Capture screenshots for verification
- **JavaScript Execution**: Run custom JavaScript code
- **Element Waiting**: Wait for elements to load before proceeding

### **Supported Browsers**
- **Chromium** (default, recommended)
- **Firefox**
- **WebKit** (Safari engine)

### **Automation Modes**
- **Headless**: Run without visible browser window (default)
- **Visible**: Run with visible browser window for debugging

## 🛠️ **Available Tools**

### **1. Web Automation Tool**
```json
{
  "name": "web_automation",
  "description": "Perform web automation tasks including navigation, clicking, and form interactions"
}
```

**Example Usage:**
```json
{
  "url": "https://example.com",
  "actions": [
    {
      "type": "click",
      "params": {
        "selector": "#login-button",
        "selector_type": "css"
      }
    },
    {
      "type": "fill_form",
      "params": {
        "form_data": {
          "#username": "myuser",
          "#password": "mypass"
        }
      }
    }
  ],
  "headless": true
}
```

### **2. Web Scraping Tool**
```json
{
  "name": "web_scraping",
  "description": "Scrape data from web pages using CSS selectors"
}
```

**Example Usage:**
```json
{
  "url": "https://news.ycombinator.com",
  "selectors": {
    "headlines": ".storylink",
    "scores": ".score",
    "comments": ".comment"
  },
  "wait_for_element": ".storylink"
}
```

### **3. Form Filling Tool**
```json
{
  "name": "form_filling",
  "description": "Fill web forms automatically"
}
```

**Example Usage:**
```json
{
  "url": "https://example.com/contact",
  "form_data": {
    "#name": "John Doe",
    "#email": "john@example.com",
    "#message": "Hello from Brebot!"
  },
  "submit_button_selector": "#submit-btn"
}
```

### **4. Screenshot Tool**
```json
{
  "name": "web_screenshot",
  "description": "Take screenshots of web pages"
}
```

**Example Usage:**
```json
{
  "url": "https://example.com",
  "filename": "homepage_screenshot.png",
  "full_page": true
}
```

## 🔄 **N8N Integration**

### **N8N Workflow Tool**
```json
{
  "name": "n8n_workflow",
  "description": "Execute n8n workflows and manage automation"
}
```

**Example Usage:**
```json
{
  "workflow_id": "workflow_123",
  "input_data": {
    "email": "user@example.com",
    "message": "Automated message"
  },
  "n8n_url": "http://localhost:5678"
}
```

### **N8N Workflow Manager**
```json
{
  "name": "n8n_workflow_manager",
  "description": "Manage n8n workflows (create, update, activate, deactivate)"
}
```

**Available Actions:**
- `list` - List all workflows
- `get` - Get workflow details
- `create` - Create new workflow
- `update` - Update existing workflow
- `activate` - Activate workflow
- `deactivate` - Deactivate workflow
- `delete` - Delete workflow

## 🎯 **Use Cases**

### **1. E-commerce Automation**
- **Product Monitoring**: Check prices, stock levels
- **Order Processing**: Automate order fulfillment
- **Inventory Management**: Update product information
- **Customer Support**: Automated form responses

### **2. Data Collection**
- **Market Research**: Scrape competitor data
- **Lead Generation**: Extract contact information
- **Content Aggregation**: Collect news, articles
- **Social Media Monitoring**: Track mentions, hashtags

### **3. Business Process Automation**
- **Form Submissions**: Automate repetitive form filling
- **Report Generation**: Collect data for reports
- **Email Automation**: Send automated emails
- **Document Processing**: Fill PDF forms, generate documents

### **4. Testing & Quality Assurance**
- **Website Testing**: Automated UI testing
- **Performance Monitoring**: Check page load times
- **Cross-browser Testing**: Test on different browsers
- **Regression Testing**: Verify functionality after changes

## 🚀 **Getting Started**

### **1. Install Dependencies**
```bash
cd /Users/bre/brebot
source venv/bin/activate
pip install playwright selenium beautifulsoup4 requests-html webdriver-manager
```

### **2. Install Browser Drivers**
```bash
# Install Playwright browsers
playwright install

# Or install specific browsers
playwright install chromium firefox webkit
```

### **3. Start N8N (Optional)**
```bash
# Using Docker
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n

# Using npm
npm install n8n -g
n8n start
```

### **4. Test Web Automation**
```python
from src.agents.web_automation_agent import WebAutomationAgent

async def test_automation():
    agent = WebAutomationAgent()
    await agent.start_browser("chromium", headless=True)
    await agent.navigate_to("https://example.com")
    screenshot = await agent.take_screenshot()
    await agent.close_browser()
    print(f"Screenshot saved: {screenshot}")

# Run the test
import asyncio
asyncio.run(test_automation())
```

## 📋 **Workflow Examples**

### **Example 1: Automated Form Submission**
```json
{
  "workflow_steps": [
    {
      "action": "navigate",
      "params": {
        "url": "https://example.com/contact"
      }
    },
    {
      "action": "fill_form",
      "params": {
        "form_data": {
          "#name": "John Doe",
          "#email": "john@example.com",
          "#message": "Automated message from Brebot"
        }
      }
    },
    {
      "action": "click",
      "params": {
        "selector": "#submit-btn"
      }
    },
    {
      "action": "screenshot",
      "params": {
        "filename": "form_submission.png"
      }
    }
  ]
}
```

### **Example 2: Data Scraping Workflow**
```json
{
  "workflow_steps": [
    {
      "action": "navigate",
      "params": {
        "url": "https://news.ycombinator.com"
      }
    },
    {
      "action": "wait",
      "params": {
        "selector": ".storylink",
        "timeout": 10
      }
    },
    {
      "action": "scrape",
      "params": {
        "selectors": {
          "headlines": ".storylink",
          "scores": ".score",
          "comments": ".comment"
        }
      }
    },
    {
      "action": "screenshot",
      "params": {
        "filename": "hn_scraped.png"
      }
    }
  ]
}
```

### **Example 3: N8N Workflow Integration**
```json
{
  "workflow_steps": [
    {
      "action": "navigate",
      "params": {
        "url": "https://api.example.com/data"
      }
    },
    {
      "action": "scrape",
      "params": {
        "selectors": {
          "data": ".api-response"
        }
      }
    },
    {
      "action": "javascript",
      "params": {
        "script": "return document.querySelector('.api-response').textContent;"
      }
    }
  ]
}
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Browser settings
export BROWSER_HEADLESS=true
export BROWSER_TYPE=chromium
export BROWSER_TIMEOUT=30000

# N8N settings
export N8N_URL=http://localhost:5678
export N8N_API_KEY=your_api_key_here

# Screenshot settings
export SCREENSHOT_DIR=/Users/bre/brebot/screenshots
export SCREENSHOT_FORMAT=png
```

### **Browser Configuration**
```python
# Custom browser options
browser_options = {
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080"
    ]
}
```

## 🛡️ **Security Considerations**

### **1. Authentication**
- Store credentials securely
- Use environment variables for sensitive data
- Implement proper session management

### **2. Rate Limiting**
- Respect website rate limits
- Implement delays between requests
- Use proper user agents

### **3. Legal Compliance**
- Check robots.txt files
- Respect website terms of service
- Implement proper data handling

### **4. Error Handling**
- Implement retry mechanisms
- Handle network timeouts
- Log all automation activities

## 📊 **Monitoring & Logging**

### **Activity Logging**
All web automation activities are logged with:
- Timestamp
- Action performed
- URL accessed
- Success/failure status
- Error messages (if any)

### **Screenshot Evidence**
- Automatic screenshots for verification
- Timestamped filenames
- Organized in `/screenshots` directory

### **Performance Metrics**
- Page load times
- Action execution times
- Success rates
- Error frequencies

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Browser Won't Start**
   ```bash
   # Install missing dependencies
   playwright install
   # Or for Selenium
   pip install webdriver-manager
   ```

2. **Element Not Found**
   - Check CSS selectors
   - Add wait conditions
   - Verify page load completion

3. **N8N Connection Failed**
   - Verify N8N is running
   - Check API key
   - Confirm network connectivity

4. **Screenshot Failures**
   - Check directory permissions
   - Verify disk space
   - Ensure browser is visible (for debugging)

### **Debug Mode**
```python
# Enable visible browser for debugging
agent = WebAutomationAgent()
await agent.start_browser("chromium", headless=False)
```

## 🔮 **Advanced Features**

### **1. Custom JavaScript Execution**
```python
result = await agent.execute_javascript("""
    return {
        title: document.title,
        url: window.location.href,
        timestamp: new Date().toISOString()
    };
""")
```

### **2. Multi-Page Workflows**
```python
# Navigate through multiple pages
pages = ["page1.html", "page2.html", "page3.html"]
for page in pages:
    await agent.navigate_to(f"https://example.com/{page}")
    data = await agent.scrape_page()
    # Process data...
```

### **3. Conditional Logic**
```python
# Wait for specific conditions
await agent.wait_for_element("#success-message", timeout=30)
if await agent.element_exists("#error-message"):
    # Handle error case
    pass
```

## 📚 **Resources**

- [Playwright Documentation](https://playwright.dev/python/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [N8N Documentation](https://docs.n8n.io/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

---

**Need help?** Check the logs in `logs/brebot.log` or open an issue on GitHub.
