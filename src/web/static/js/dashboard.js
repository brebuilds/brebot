/**
 * Enhanced Brebot Dashboard JavaScript
 * Three-panel interface with real-time updates
 */

function dashboardApp() {
    return {
        // State
        systemStatus: 'checking',
        selectedBot: 'brebot',
        selectedBotId: null,
        useRAG: true,
        chatInput: '',
        chatMessages: [],
        bots: [],
        activeTasks: [],
        activePipelines: [],
        recentFiles: [],
        showUploadModal: false,
        showSetupPanel: false,
        powerStatus: null,
        powerLoading: false,
        ingestionHistory: [],
        ingestionLoading: false,
        uploadingIngestion: false,
        dropActive: false,
        showMemoryManager: false,
        showBotEditor: false,
        showCreateBotModal: false,
        showBotArchitectModal: false,
        botArchitectLoading: false,
        botArchitectForm: {
            name: '',
            goal: '',
            description: '',
            primary_tasks: '',
            data_sources: '',
            integrations: '',
            success_metrics: '',
            personality: '',
            auto_create: false,
        },
        botArchitectResult: null,
        showToolManager: false,
        websocket: null,
        
        // Connection management
        showConnectionsModal: false,
        connections: [],
        darkMode: localStorage.getItem('darkMode') === 'true',
        
        // Code Editor
        showCodeEditor: false,
        showIntegrationsManager: false,
        showPlatformConfig: false,
        integrations: {},
        integrationSummary: { total: 0, enabled: 0, healthy: 0 },
        activityCount: 0,
        selectedPlatform: null,
        platformConfig: { api_key: '', enabled: true, shop_id: '', base_url: '' },
        
        // Theme Management
        showThemeManager: false,
        availableThemes: {},
        selectedTheme: 'default',
        customTheme: {
            name: 'Custom Theme',
            primary_color: '#3b82f6',
            secondary_color: '#64748b',
            accent_color: '#10b981',
            background_color: '#ffffff',
            text_color: '#1f2937',
            font_family: 'Inter, system-ui, sans-serif',
            logo_url: null,
            custom_css: ''
        },
        codeFiles: [],
        selectedFile: null,
        fileModified: false,
        monacoEditor: null,
        currentFileContent: '',
        
        // Memory management
        memoryUsage: 65,
        memoryStats: {
            total: 1247,
            used: 810,
            indexed: 756
        },
        memoryCategories: [
            { name: 'Documents', icon: 'fas fa-file-alt', count: 456 },
            { name: 'Images', icon: 'fas fa-image', count: 234 },
            { name: 'Code', icon: 'fas fa-code', count: 123 },
            { name: 'Web Content', icon: 'fas fa-globe', count: 89 }
        ],
        
        // File ingestion
        selectedSources: {
            dropbox: false,
            googleDrive: false,
            notion: false
        },
        
        // Bot hierarchy
        botHierarchy: [
            {
                name: 'Content Creation',
                icon: 'fas fa-pen-fancy',
                status: 'healthy',
                expanded: true,
                bots: [
                    { bot_id: 'mocktopus', description: 'Mockup and design generation', responsibilities: 'Create product mockups, design assets, and visual content', status: 'online', health_score: 95, tasks_completed: 234, avatar: null },
                    { bot_id: 'content-writer', description: 'Content writing and editing', responsibilities: 'Write blog posts, product descriptions, and marketing copy', status: 'busy', health_score: 88, tasks_completed: 156, avatar: null }
                ]
            },
            {
                name: 'Data Management',
                icon: 'fas fa-database',
                status: 'healthy',
                expanded: false,
                bots: [
                    { bot_id: 'airtable-logger', description: 'Airtable data synchronization', responsibilities: 'Sync data between systems and maintain Airtable records', status: 'online', health_score: 92, tasks_completed: 445, avatar: null },
                    { bot_id: 'file-organizer', description: 'File organization and management', responsibilities: 'Organize files, create folders, and maintain file structure', status: 'online', health_score: 78, tasks_completed: 89, avatar: null }
                ]
            },
            {
                name: 'E-commerce',
                icon: 'fas fa-shopping-cart',
                status: 'warning',
                expanded: false,
                bots: [
                    { bot_id: 'shopify-publisher', description: 'Shopify product publishing', responsibilities: 'Publish products to Shopify, manage inventory, and sync data', status: 'busy', health_score: 67, tasks_completed: 78, avatar: null }
                ]
            }
        ],
        
        // Bot editing
        editingBot: null,
        
        // Bot creation
        newBot: {
            bot_id: '',
            department: '',
            bot_type: '',
            description: '',
            responsibilities: '',
            status: 'online',
            health_score: 100,
            tasks_completed: 0,
            selectedTools: [],
            voice: {
                provider: 'openai',
                voice_id: 'alloy',
                speed: 1.0,
                pitch: 1.0
            }
        },
        
        // Tool categories
        toolCategories: [
            {
                name: 'File Management',
                expanded: true,
                tools: [
                    { name: 'ListFilesTool', description: 'List files in directories', type: 'file' },
                    { name: 'CreateFolderTool', description: 'Create new directories', type: 'file' },
                    { name: 'MoveFileTool', description: 'Move files between locations', type: 'file' },
                    { name: 'OrganizeFilesTool', description: 'Automatically organize files', type: 'file' },
                    { name: 'DeleteFileTool', description: 'Delete files and folders', type: 'file' }
                ]
            },
            {
                name: 'Web & API',
                expanded: false,
                tools: [
                    { name: 'WebScrapingTool', description: 'Scrape content from websites', type: 'web' },
                    { name: 'APICallTool', description: 'Make HTTP API requests', type: 'web' },
                    { name: 'WebSearchTool', description: 'Search the web for information', type: 'web' },
                    { name: 'EmailTool', description: 'Send and receive emails', type: 'web' }
                ]
            },
            {
                name: 'Browser Automation',
                expanded: false,
                tools: [
                    { name: 'WebAutomationTool', description: 'Automate browser interactions', type: 'browser' },
                    { name: 'FormFillingTool', description: 'Fill web forms automatically', type: 'browser' },
                    { name: 'ScreenshotTool', description: 'Take web page screenshots', type: 'browser' },
                    { name: 'WebWorkflowTool', description: 'Execute complex web workflows', type: 'browser' }
                ]
            },
            {
                name: 'Workflow Automation',
                expanded: false,
                tools: [
                    { name: 'N8NWorkflowTool', description: 'Execute n8n workflows', type: 'workflow' },
                    { name: 'N8NWorkflowManagerTool', description: 'Manage n8n workflows', type: 'workflow' },
                    { name: 'WorkflowSchedulerTool', description: 'Schedule automated workflows', type: 'workflow' },
                    { name: 'WorkflowMonitorTool', description: 'Monitor workflow execution', type: 'workflow' }
                ]
            },
            {
                name: 'Data Processing',
                expanded: false,
                tools: [
                    { name: 'DataAnalysisTool', description: 'Analyze and process data', type: 'data' },
                    { name: 'CSVProcessorTool', description: 'Process CSV files', type: 'data' },
                    { name: 'JSONProcessorTool', description: 'Process JSON data', type: 'data' },
                    { name: 'DatabaseTool', description: 'Database operations', type: 'data' }
                ]
            },
            {
                name: 'Content Creation',
                expanded: false,
                tools: [
                    { name: 'TextGeneratorTool', description: 'Generate text content', type: 'content' },
                    { name: 'ImageGeneratorTool', description: 'Generate images', type: 'content' },
                    { name: 'MarkdownTool', description: 'Create markdown documents', type: 'content' },
                    { name: 'PDFTool', description: 'Create and process PDFs', type: 'content' }
                ]
            },
            {
                name: 'E-commerce',
                expanded: false,
                tools: [
                    { name: 'ShopifyTool', description: 'Shopify store management', type: 'ecommerce' },
                    { name: 'ProductCatalogTool', description: 'Manage product catalogs', type: 'ecommerce' },
                    { name: 'InventoryTool', description: 'Track inventory levels', type: 'ecommerce' },
                    { name: 'OrderProcessingTool', description: 'Process orders', type: 'ecommerce' }
                ]
            },
            {
                name: 'Communication',
                expanded: false,
                tools: [
                    { name: 'SlackTool', description: 'Slack integration', type: 'comm' },
                    { name: 'DiscordTool', description: 'Discord bot integration', type: 'comm' },
                    { name: 'TeamsTool', description: 'Microsoft Teams integration', type: 'comm' },
                    { name: 'NotificationTool', description: 'Send notifications', type: 'comm' }
                ]
            }
        ],
        
        // Computed properties
        get onlineBots() {
            return this.botHierarchy.flatMap(dept => dept.bots).filter(bot => bot.status === 'online').length;
        },
        
        get busyBots() {
            return this.botHierarchy.flatMap(dept => dept.bots).filter(bot => bot.status === 'busy').length;
        },
        
        get selectedSourcesCount() {
            return Object.values(this.selectedSources).filter(Boolean).length;
        },
        
        // Initialize
        init() {
            this.loadInitialData();
            this.connectWebSocket();
            this.startPeriodicUpdates();
            this.applyDarkMode();
            this.loadConnections();
            this.fetchIngestionHistory();
            this.refreshCodeFiles();

            // Add welcome message (only if no messages exist)
            if (this.chatMessages.length === 0) {
                this.addChatMessage('system', 'Hey there BreHuman! What\'s up?');
            }
        },
        
        // Dark mode functions
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('darkMode', this.darkMode);
            this.applyDarkMode();
        },
        
        applyDarkMode() {
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        },
        
        // Memory management methods
        optimizeMemory() {
            this.showNotification('Optimizing memory...', 'info');
            // Simulate memory optimization
            setTimeout(() => {
                this.memoryUsage = Math.max(0, this.memoryUsage - 10);
                this.showNotification('Memory optimized successfully!', 'success');
            }, 2000);
        },
        
        clearMemory() {
            if (confirm('Are you sure you want to clear all memory? This action cannot be undone.')) {
                this.showNotification('Clearing memory...', 'info');
                setTimeout(() => {
                    this.memoryStats.used = 0;
                    this.memoryUsage = 0;
                    this.showNotification('Memory cleared successfully!', 'success');
                }, 1500);
            }
        },
        
        clearCategory(categoryName) {
            if (confirm(`Clear all ${categoryName} from memory?`)) {
                this.showNotification(`Clearing ${categoryName}...`, 'info');
                const category = this.memoryCategories.find(c => c.name === categoryName);
                if (category) {
                    category.count = 0;
                }
                setTimeout(() => {
                    this.showNotification(`${categoryName} cleared!`, 'success');
                }, 1000);
            }
        },

        // Bot architect helpers
        resetBotArchitectForm() {
            this.botArchitectForm = {
                name: '',
                goal: '',
                description: '',
                primary_tasks: '',
                data_sources: '',
                integrations: '',
                success_metrics: '',
                personality: '',
                auto_create: false,
            };
            this.botArchitectResult = null;
        },

        openBotArchitect() {
            this.resetBotArchitectForm();
            this.showBotArchitectModal = true;
        },

        closeBotArchitect() {
            this.showBotArchitectModal = false;
        },

        parseListInput(value) {
            if (!value) return [];
            return value
                .split(/[,\n]/g)
                .map(item => item.trim())
                .filter(Boolean);
        },

        addBotToHierarchy(bot, departmentName = 'Automation') {
            const normalizedId = bot.bot_id || bot.id;
            let department = this.botHierarchy.find(d => d.name === departmentName);
            if (!department) {
                department = {
                    name: departmentName,
                    icon: 'fas fa-robot',
                    status: 'healthy',
                    expanded: true,
                    bots: [],
                };
                this.botHierarchy.push(department);
            }

            const existing = department.bots.find(existingBot => existingBot.bot_id === normalizedId);
            if (!existing) {
                department.bots.push({
                    bot_id: normalizedId,
                    description: bot.description || '',
                    responsibilities: Array.isArray(bot.responsibilities)
                        ? bot.responsibilities.join('\n')
                        : (bot.responsibilities || ''),
                    status: bot.status || 'online',
                    health_score: bot.health_score || 100,
                    tasks_completed: bot.tasks_completed || 0,
                    avatar: bot.avatar || null,
                    tools: bot.tools || [],
                });
            }
        },

        async submitBotArchitect(autoCreate = false) {
            if (!this.botArchitectForm.goal.trim()) {
                this.showNotification('Please describe the bot\'s main goal.', 'error');
                return;
            }

            this.botArchitectLoading = true;
            try {
                const payload = {
                    goal: this.botArchitectForm.goal.trim(),
                    description: this.botArchitectForm.description.trim() || null,
                    name: this.botArchitectForm.name.trim() || null,
                    primary_tasks: this.parseListInput(this.botArchitectForm.primary_tasks),
                    data_sources: this.parseListInput(this.botArchitectForm.data_sources),
                    integrations: this.parseListInput(this.botArchitectForm.integrations),
                    success_metrics: this.parseListInput(this.botArchitectForm.success_metrics),
                    personality: this.botArchitectForm.personality.trim() || null,
                    auto_create: autoCreate || this.botArchitectForm.auto_create,
                };

                const response = await fetch('/api/bots/architect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Failed to generate bot blueprint');
                }

                this.botArchitectResult = data;

                if (data.created_bot) {
                    this.addBotToHierarchy(data.created_bot, data.recommendation?.department);
                    this.showNotification(`Bot "${data.created_bot.id || data.created_bot.bot_id}" created!`, 'success');
                } else {
                    this.showNotification('Bot blueprint ready', 'success');
                }
            } catch (error) {
                console.error('Error designing bot:', error);
                this.showNotification(error.message || 'Bot design failed', 'error');
            } finally {
                this.botArchitectLoading = false;
            }
        },
        
        // Setup panel + ingestion
        openSetupPanel() {
            this.showSetupPanel = true;
            this.fetchIngestionHistory();
        },

        closeSetupPanel() {
            this.showSetupPanel = false;
        },

        async powerUpSystem() {
            try {
                this.powerLoading = true;
                const response = await fetch('/api/system/power-up', { method: 'POST' });
                this.powerStatus = await response.json();
                if (!response.ok) {
                    throw new Error('Power-up returned an error');
                }
                this.showNotification('System power-up complete!', 'success');
            } catch (error) {
                console.error('Error powering up system:', error);
                this.showNotification('Failed to power up system', 'error');
            } finally {
                this.powerLoading = false;
            }
        },

        async fetchIngestionHistory() {
            try {
                const response = await fetch('/api/ingest/runs');
                if (!response.ok) return;
                const data = await response.json();
                this.ingestionHistory = data.runs || [];
            } catch (error) {
                console.error('Error loading ingestion history:', error);
            }
        },

        async triggerIngestion(dryRun = false) {
            try {
                this.ingestionLoading = true;
                const response = await fetch('/api/ingest/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dry_run: dryRun }),
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Failed to start ingestion');
                }
                this.showNotification(dryRun ? 'Dry-run queued' : 'Ingestion started', 'success');
            } catch (error) {
                console.error('Error starting ingestion:', error);
                this.showNotification('Failed to start ingestion', 'error');
            } finally {
                this.ingestionLoading = false;
            }
        },

        async uploadIngestionFilesFromInput(event) {
            const files = event.target.files ? Array.from(event.target.files) : [];
            if (!files.length) return;
            await this.uploadIngestionFiles(files);
            event.target.value = '';
        },

        async uploadIngestionFiles(files) {
            if (!files.length) return;
            try {
                this.uploadingIngestion = true;
                const formData = new FormData();
                files.forEach(file => formData.append('files', file, file.name));
                const response = await fetch('/api/ingest/upload', {
                    method: 'POST',
                    body: formData,
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Upload failed');
                }
                this.showNotification(`Uploaded ${data.saved_files.length} file(s)`, 'success');
            } catch (error) {
                console.error('Error uploading files:', error);
                this.showNotification('Failed to upload files', 'error');
            } finally {
                this.uploadingIngestion = false;
                this.dropActive = false;
            }
        },

        handleDragOver(event) {
            event.preventDefault();
            this.dropActive = true;
        },

        handleDragLeave(event) {
            event.preventDefault();
            this.dropActive = false;
        },

        handleDrop(event) {
            event.preventDefault();
            this.dropActive = false;
            const files = event.dataTransfer ? Array.from(event.dataTransfer.files) : [];
            if (files.length) {
                this.uploadIngestionFiles(files);
            }
        },
        
        // Bot hierarchy methods
        toggleDepartment(departmentName) {
            const department = this.botHierarchy.find(d => d.name === departmentName);
            if (department) {
                department.expanded = !department.expanded;
            }
        },
        
        selectBotNode(bot) {
            this.selectedBotId = bot.bot_id;
            this.selectedBot = bot.bot_id;
            this.showNotification(`Selected ${bot.bot_id}`, 'info');
        },
        
        editBot(bot) {
            this.editingBot = { ...bot };
            this.showBotEditor = true;
        },
        
        saveBot() {
            // Find and update the bot in the hierarchy
            for (const department of this.botHierarchy) {
                const botIndex = department.bots.findIndex(b => b.bot_id === this.editingBot.bot_id);
                if (botIndex !== -1) {
                    department.bots[botIndex] = { ...this.editingBot };
                    break;
                }
            }
            
            this.showBotEditor = false;
            this.showNotification('Bot updated successfully!', 'success');
        },
        
        uploadBotAvatar() {
            // Simulate file upload
            this.showNotification('Uploading avatar...', 'info');
            setTimeout(() => {
                this.editingBot.avatar = 'https://via.placeholder.com/64x64/3b82f6/ffffff?text=' + this.editingBot.bot_id.charAt(0).toUpperCase();
                this.showNotification('Avatar uploaded successfully!', 'success');
            }, 1500);
        },
        
        // Bot creation methods
        createBot() {
            // Validate required fields
            if (!this.newBot.bot_id || !this.newBot.department || !this.newBot.bot_type || !this.newBot.description) {
                this.showNotification('Please fill in all required fields', 'error');
                return;
            }
            
            // Check if bot ID already exists
            const existingBot = this.botHierarchy.flatMap(dept => dept.bots).find(bot => bot.bot_id === this.newBot.bot_id);
            if (existingBot) {
                this.showNotification('Bot ID already exists. Please choose a different name.', 'error');
                return;
            }
            
            // Create new bot object
            const newBot = {
                bot_id: this.newBot.bot_id,
                description: this.newBot.description,
                responsibilities: this.newBot.responsibilities,
                status: this.newBot.status,
                health_score: this.newBot.health_score,
                tasks_completed: 0,
                avatar: null,
                tools: [...this.newBot.selectedTools],
                voice: {...this.newBot.voice}
            };
            
            // Find the department and add the bot
            const department = this.botHierarchy.find(dept => dept.name === this.newBot.department);
            if (department) {
                department.bots.push(newBot);
                this.showNotification(`Bot "${newBot.bot_id}" created successfully!`, 'success');
            } else {
                // Create new department if it doesn't exist
                this.botHierarchy.push({
                    name: this.newBot.department,
                    icon: 'fas fa-folder',
                    status: 'healthy',
                    expanded: true,
                    bots: [newBot]
                });
                this.showNotification(`Bot "${newBot.bot_id}" created in new department "${this.newBot.department}"!`, 'success');
            }
            
            // Configure voice for the bot
            this.configureBotVoice(newBot.bot_id, newBot.voice);
            
            // Reset form
            this.resetNewBotForm();
            this.showCreateBotModal = false;
        },
        
        resetNewBotForm() {
            this.newBot = {
                bot_id: '',
                department: '',
                bot_type: '',
                description: '',
                responsibilities: '',
                status: 'online',
                health_score: 100,
                tasks_completed: 0,
                selectedTools: [],
                voice: {
                    provider: 'openai',
                    voice_id: 'alloy',
                    speed: 1.0,
                    pitch: 1.0
                }
            };
        },
        
        async configureBotVoice(botId, voiceConfig) {
            try {
                const response = await fetch(`/api/voice/configure?bot_id=${botId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(voiceConfig)
                });
                
                if (response.ok) {
                    console.log(`Voice configured for bot ${botId}`);
                } else {
                    console.error('Failed to configure voice for bot:', botId);
                }
            } catch (error) {
                console.error('Error configuring voice:', error);
            }
        },
        
        // Tool management methods
        toggleToolCategory(categoryName) {
            const category = this.toolCategories.find(cat => cat.name === categoryName);
            if (category) {
                category.expanded = !category.expanded;
            }
        },
        
        selectAllToolsInCategory(categoryName) {
            const category = this.toolCategories.find(cat => cat.name === categoryName);
            if (category) {
                const categoryTools = category.tools.map(tool => tool.name);
                const allSelected = categoryTools.every(tool => this.newBot.selectedTools.includes(tool));
                
                if (allSelected) {
                    // Deselect all tools in this category
                    this.newBot.selectedTools = this.newBot.selectedTools.filter(tool => !categoryTools.includes(tool));
                } else {
                    // Select all tools in this category
                    categoryTools.forEach(tool => {
                        if (!this.newBot.selectedTools.includes(tool)) {
                            this.newBot.selectedTools.push(tool);
                        }
                    });
                }
            }
        },
        
        // Tool management methods
        getTotalTools() {
            return this.toolCategories.reduce((total, category) => total + category.tools.length, 0);
        },
        
        getActiveTools() {
            return this.toolCategories.reduce((total, category) => {
                return total + category.tools.filter(tool => this.getToolStatus(tool.name) === 'Active').length;
            }, 0);
        },
        
        getToolsInUse() {
            // Count tools that are being used by bots
            const allBots = this.botHierarchy.flatMap(dept => dept.bots);
            const usedTools = new Set();
            allBots.forEach(bot => {
                if (bot.tools) {
                    bot.tools.forEach(tool => usedTools.add(tool));
                }
            });
            return usedTools.size;
        },
        
        // Connection statistics
        connectedCount() {
            return this.connections.filter(conn => conn.status === 'connected').length;
        },
        
        ingestionEnabledCount() {
            return this.connections.filter(conn => conn.enabled_for_ingestion).length;
        },
        
        webhookCount() {
            return this.connections.filter(conn => conn.n8n_webhook_url).length;
        },
        
        getCategoryIcon(categoryName) {
            const icons = {
                'File Management': 'fas fa-folder',
                'Web & API': 'fas fa-globe',
                'Browser Automation': 'fas fa-mouse-pointer',
                'Workflow Automation': 'fas fa-project-diagram',
                'Data Processing': 'fas fa-database',
                'Content Creation': 'fas fa-pen-fancy',
                'E-commerce': 'fas fa-shopping-cart',
                'Communication': 'fas fa-comments'
            };
            return icons[categoryName] || 'fas fa-tools';
        },
        
        getToolStatus(toolName) {
            // Simulate tool status - in real implementation, this would check actual tool status
            const statuses = ['Active', 'Inactive', 'Error', 'Maintenance'];
            const hash = toolName.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
            return statuses[hash % statuses.length];
        },
        
        getToolStatusClass(toolName) {
            const status = this.getToolStatus(toolName);
            const classes = {
                'Active': 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200',
                'Inactive': 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200',
                'Error': 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200',
                'Maintenance': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200'
            };
            return classes[status] || classes['Inactive'];
        },
        
        toggleToolStatus(toolName) {
            this.showNotification(`Tool "${toolName}" status toggled`, 'info');
            // In real implementation, this would make an API call to toggle tool status
        },
        
        enableAllTools() {
            this.showNotification('Enabling all tools...', 'info');
            setTimeout(() => {
                this.showNotification('All tools enabled successfully!', 'success');
            }, 1500);
        },
        
        disableAllTools() {
            this.showNotification('Disabling all tools...', 'info');
            setTimeout(() => {
                this.showNotification('All tools disabled successfully!', 'success');
            }, 1500);
        },
        
        refreshToolStatus() {
            this.showNotification('Refreshing tool status...', 'info');
            setTimeout(() => {
                this.showNotification('Tool status refreshed!', 'success');
            }, 1000);
        },
        
        // Connection management methods
        async loadConnections() {
            try {
                const response = await fetch('/api/connections');
                const data = await response.json();
                this.connections = data.connections;
            } catch (error) {
                console.error('Error loading connections:', error);
                this.showNotification('Failed to load connections', 'error');
            }
        },
        
        async connectConnection(connectionId) {
            try {
                const response = await fetch(`/api/connections/${connectionId}/connect`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.oauth_url) {
                    // Open OAuth URL in new window
                    window.open(data.oauth_url, 'oauth', 'width=600,height=600');
                    this.showNotification('OAuth window opened. Complete authorization to connect.', 'info');
                } else {
                    this.showNotification('Failed to initiate connection', 'error');
                }
            } catch (error) {
                console.error('Error connecting:', error);
                this.showNotification('Failed to connect', 'error');
            }
        },
        
        async disconnectConnection(connectionId) {
            try {
                const response = await fetch(`/api/connections/${connectionId}/disconnect`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.showNotification('Connection disconnected successfully', 'success');
                    await this.loadConnections(); // Refresh connections
                } else {
                    this.showNotification('Failed to disconnect', 'error');
                }
            } catch (error) {
                console.error('Error disconnecting:', error);
                this.showNotification('Failed to disconnect', 'error');
            }
        },
        
        async toggleIngestion(connectionId, enabled) {
            try {
                const response = await fetch(`/api/connections/${connectionId}/toggle-ingestion`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ enabled })
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.showNotification(data.message, 'success');
                    await this.loadConnections(); // Refresh connections
                } else {
                    this.showNotification('Failed to toggle ingestion', 'error');
                }
            } catch (error) {
                console.error('Error toggling ingestion:', error);
                this.showNotification('Failed to toggle ingestion', 'error');
            }
        },
        
        async checkConnectionHealth(connectionId) {
            try {
                const response = await fetch(`/api/connections/${connectionId}/health`);
                const data = await response.json();
                
                if (data.is_healthy) {
                    this.showNotification(`Connection is healthy (${data.response_time_ms}ms)`, 'success');
                } else {
                    this.showNotification(`Connection health check failed: ${data.error_details}`, 'error');
                }
            } catch (error) {
                console.error('Error checking health:', error);
                this.showNotification('Failed to check connection health', 'error');
            }
        },
        
        async refreshConnections() {
            await this.loadConnections();
            this.showNotification('Connections refreshed', 'success');
        },
        
        formatDate(dateString) {
            if (!dateString) return 'Never';
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        },
        
        // Notification system
        showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 ${
                type === 'success' ? 'bg-green-500 text-white' :
                type === 'error' ? 'bg-red-500 text-white' :
                type === 'warning' ? 'bg-yellow-500 text-white' :
                'bg-blue-500 text-white'
            }`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            // Remove after 3 seconds
            setTimeout(() => {
                notification.remove();
            }, 3000);
        },
        
        // Data loading
        async loadInitialData() {
            try {
                await Promise.all([
                    this.loadSystemStatus(),
                    this.loadBots(),
                    this.loadFiles(),
                    this.loadActiveTasks(),
                    this.loadActivePipelines()
                ]);
            } catch (error) {
                console.error('Error loading initial data:', error);
            }
        },
        
        async loadSystemStatus() {
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                this.systemStatus = data.status;
                
                // Update bot statuses from health check
                if (data.bots) {
                    this.bots = Object.values(data.bots);
                }
            } catch (error) {
                console.error('Error loading system status:', error);
                this.systemStatus = 'error';
            }
        },
        
        async loadBots() {
            try {
                const response = await fetch('/api/bots');
                const data = await response.json();
                this.bots = Object.values(data.bots);
            } catch (error) {
                console.error('Error loading bots:', error);
            }
        },
        
        async loadFiles() {
            try {
                const response = await fetch('/api/files');
                const data = await response.json();
                this.recentFiles = data.files.slice(0, 5); // Show only recent 5 files
            } catch (error) {
                console.error('Error loading files:', error);
            }
        },
        
        async loadActiveTasks() {
            try {
                const response = await fetch('/api/tasks');
                const data = await response.json();
                this.activeTasks = data.tasks.filter(task => 
                    task.status === 'running' || task.status === 'pending'
                );
            } catch (error) {
                console.error('Error loading active tasks:', error);
            }
        },
        
        async loadActivePipelines() {
            // Simulate active pipelines
            this.activePipelines = [
                {
                    id: 'pipeline_001',
                    type: 'Design → Shopify',
                    progress: 45,
                    current_step: 'Mockup Generation',
                    status: 'running'
                },
                {
                    id: 'pipeline_002',
                    type: 'Content Creation',
                    progress: 80,
                    current_step: 'Final Review',
                    status: 'running'
                }
            ];
        },
        
        // WebSocket connection
        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.sendPing();
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected, reconnecting...');
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        },
        
        handleWebSocketMessage(data) {
            switch (data.type) {
                case 'task_update':
                    this.updateTask(data.task);
                    break;
                case 'ingestion_runs':
                    this.ingestionHistory = data.runs || [];
                    break;
                case 'bot_response':
                    this.handleBotResponse(data);
                    break;
                case 'bot_error':
                    this.handleBotError(data);
                    break;
                case 'pong':
                    // Keep connection alive
                    break;
                default:
                    console.log('Unknown WebSocket message type:', data.type);
            }
        },
        
        sendPing() {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({ type: 'ping' }));
            }
        },
        
        // Chat functionality
        async sendMessage() {
            if (!this.chatInput.trim()) return;
            
            const message = this.chatInput.trim();
            this.chatInput = '';
            
            // Add user message
            this.addChatMessage('user', message);
            
            // Send to backend
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        context: this.selectedBot,
                        use_rag: this.useRAG
                    })
                });
                
                const data = await response.json();
                
                // Poll for result
                this.pollChatResult(data.task_id);
                
            } catch (error) {
                console.error('Error sending message:', error);
                this.addChatMessage('system', 'Sorry, I encountered an error. Please try again.');
            }
        },
        
        async pollChatResult(taskId) {
            const maxAttempts = 30;
            let attempts = 0;
            
            const poll = async () => {
                try {
                    const response = await fetch(`/api/chat/${taskId}`);
                    const task = await response.json();
                    
                    if (task.status === 'completed') {
                        this.addChatMessage('brebot', task.result.response);
                        return;
                    } else if (task.status === 'failed') {
                        this.addChatMessage('system', 'Sorry, I encountered an error processing your request.');
                        return;
                    }
                    
                    attempts++;
                    if (attempts < maxAttempts) {
                        setTimeout(poll, 1000);
                    } else {
                        this.addChatMessage('system', 'Request timed out. Please try again.');
                    }
                } catch (error) {
                    console.error('Error polling chat result:', error);
                    this.addChatMessage('system', 'Sorry, I encountered an error. Please try again.');
                }
            };
            
            poll();
        },
        
        addChatMessage(sender, text) {
            this.chatMessages.push({
                id: Date.now(),
                sender: sender,
                text: text,
                timestamp: new Date().toLocaleTimeString()
            });
            
            // Scroll to bottom
            this.$nextTick(() => {
                const chatContainer = document.querySelector('.overflow-y-auto');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            });
        },
        
        // Bot management
        selectBot(bot) {
            this.selectedBotId = bot.bot_id;
            this.selectedBot = bot.bot_id;
            this.addChatMessage('system', `Switched context to ${bot.bot_id}. How can I help you?`);
        },
        
        async sendBotCommand(botId, command, parameters = {}) {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({
                    type: 'bot_command',
                    bot_id: botId,
                    command: command,
                    parameters: parameters
                }));
            }
        },
        
        handleBotResponse(data) {
            this.addChatMessage(data.bot_id, data.result);
        },
        
        handleBotError(data) {
            this.addChatMessage('system', `Error from ${data.bot_id}: ${data.error}`);
        },
        
        // File operations
        selectFile(file) {
            this.addChatMessage('user', `Selected file: ${file.name}`);
            // In a real implementation, this would load file details or start processing
        },
        
        async refreshFiles() {
            await this.loadFiles();
            this.addChatMessage('system', 'File explorer refreshed');
        },
        
        async init() {
            // Load initial data
            await this.loadFiles();
            await this.refreshIntegrations();
            await this.loadThemes();
            this.loadConnections();
            this.loadBots();
        },
        
        async uploadFile() {
            // Simulate file upload
            this.showUploadModal = false;
            this.addChatMessage('system', 'File upload started...');
            await this.refreshFiles();
        },
        
        // Pipeline operations
        async startPipeline(pipelineType) {
            try {
                const response = await fetch('/api/pipeline/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        pipeline_type: pipelineType,
                        input_data: {
                            source: 'file_explorer',
                            timestamp: new Date().toISOString()
                        },
                        priority: 'normal'
                    })
                });
                
                const data = await response.json();
                this.addChatMessage('system', `Started ${pipelineType} pipeline (ID: ${data.pipeline_id})`);
                
                // Add to active pipelines
                this.activePipelines.push({
                    id: data.pipeline_id,
                    type: pipelineType,
                    progress: 0,
                    current_step: 'Initializing',
                    status: 'running'
                });
                
            } catch (error) {
                console.error('Error starting pipeline:', error);
                this.addChatMessage('system', 'Failed to start pipeline. Please try again.');
            }
        },
        
        async organizeFiles() {
            try {
                const response = await fetch('/api/files/operation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        operation: 'organize',
                        path: '/workspace',
                        parameters: {
                            method: 'extension',
                            create_folders: true
                        }
                    })
                });
                
                const data = await response.json();
                this.addChatMessage('system', 'File organization started...');
                
            } catch (error) {
                console.error('Error organizing files:', error);
                this.addChatMessage('system', 'Failed to organize files. Please try again.');
            }
        },
        
        // Task management
        updateTask(task) {
            const existingIndex = this.activeTasks.findIndex(t => t.task_id === task.task_id);
            
            if (existingIndex >= 0) {
                this.activeTasks[existingIndex] = task;
            } else {
                this.activeTasks.push(task);
            }
            
            // Remove completed tasks after a delay
            if (task.status === 'completed' || task.status === 'failed') {
                setTimeout(() => {
                    this.activeTasks = this.activeTasks.filter(t => t.task_id !== task.task_id);
                }, 5000);
            }
        },
        
        // Utility functions
        getFileIcon(fileType) {
            const icons = {
                'image': 'fas fa-image text-blue-500',
                'spreadsheet': 'fas fa-file-excel text-green-500',
                'document': 'fas fa-file-alt text-gray-500',
                'pdf': 'fas fa-file-pdf text-red-500',
                'video': 'fas fa-video text-purple-500',
                'audio': 'fas fa-music text-pink-500'
            };
            return icons[fileType] || 'fas fa-file text-gray-500';
        },
        
        formatTime(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            
            if (diff < 60000) return 'Just now';
            if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
            if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
            return date.toLocaleDateString();
        },
        
        toggleRAG() {
            this.useRAG = !this.useRAG;
            this.addChatMessage('system', 
                this.useRAG ? 'RAG enabled - I can now access the knowledge base' : 'RAG disabled - direct chat mode'
            );
        },
        
        async refreshSystemStatus() {
            await this.loadSystemStatus();
        },
        
        // Periodic updates
        startPeriodicUpdates() {
            // Update system status every 30 seconds
            setInterval(() => {
                this.loadSystemStatus();
                this.sendPing();
            }, 30000);
            
            // Update active tasks every 10 seconds
            setInterval(() => {
                this.loadActiveTasks();
            }, 10000);
        },
        
        // Code Editor Methods
        async refreshCodeFiles() {
            try {
                const response = await fetch('/api/code/browse');
                const data = await response.json();
                this.codeFiles = data.files;
            } catch (error) {
                console.error('Failed to load code files:', error);
            }
        },
        
        async loadCodeFile(filePath) {
            try {
                const response = await fetch(`/api/code/read/${encodeURIComponent(filePath)}`);
                const data = await response.json();
                
                this.selectedFile = filePath;
                this.currentFileContent = data.content;
                this.fileModified = false;
                
                // Initialize Monaco editor if not already done and editor is visible
                if (!this.monacoEditor && this.showCodeEditor) {
                    // Wait a bit for the DOM to be ready
                    setTimeout(() => this.initMonacoEditor(), 200);
                } else if (this.monacoEditor) {
                    // Update editor content
                    this.monacoEditor.setValue(data.content);
                    this.monacoEditor.setModel(
                        monaco.editor.createModel(data.content, data.language, monaco.Uri.file(filePath))
                    );
                }
            } catch (error) {
                console.error('Failed to load file:', error);
                alert('Failed to load file: ' + error.message);
            }
        },
        
        initMonacoEditor() {
            // Wait for DOM element to be available
            setTimeout(() => {
                const editorContainer = document.getElementById('monaco-editor');
                if (!editorContainer) return;
                
                require.config({ paths: { vs: 'https://unpkg.com/monaco-editor@0.44.0/min/vs' } });
                require(['vs/editor/editor.main'], () => {
                    this.monacoEditor = monaco.editor.create(editorContainer, {
                        value: this.currentFileContent,
                        language: 'python',
                        theme: this.darkMode ? 'vs-dark' : 'vs',
                        automaticLayout: true,
                        fontSize: 14,
                        minimap: { enabled: true },
                        scrollBeyondLastLine: false,
                        wordWrap: 'on',
                        formatOnPaste: true,
                        formatOnType: true
                    });
                    
                    // Track changes
                    this.monacoEditor.onDidChangeModelContent(() => {
                        this.fileModified = this.monacoEditor.getValue() !== this.currentFileContent;
                    });
                });
            }, 100);
        },
        
        async saveCurrentFile() {
            if (!this.selectedFile || !this.monacoEditor) return;
            
            try {
                const content = this.monacoEditor.getValue();
                const response = await fetch('/api/code/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        path: this.selectedFile,
                        content: content,
                        language: 'python'
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    this.currentFileContent = content;
                    this.fileModified = false;
                    alert('File saved successfully!');
                } else {
                    alert('Failed to save file: ' + result.error);
                }
            } catch (error) {
                console.error('Failed to save file:', error);
                alert('Failed to save file: ' + error.message);
            }
        },
        
        formatCode() {
            if (!this.monacoEditor) return;
            this.monacoEditor.getAction('editor.action.formatDocument').run();
        },

        // ===========================
        // INTEGRATIONS METHODS
        // ===========================

        async refreshIntegrations() {
            try {
                const response = await fetch('/api/integrations');
                const data = await response.json();
                
                this.integrations = data.integrations;
                this.integrationSummary = data.summary;
                this.activityCount = data.activity_summary?.total_activities || 0;
                
            } catch (error) {
                console.error('Failed to refresh integrations:', error);
                alert('Failed to refresh integrations: ' + error.message);
            }
        },

        async runHealthCheck() {
            try {
                const response = await fetch('/api/integrations/health-check', {
                    method: 'POST'
                });
                const data = await response.json();
                
                alert(`Health Check Complete:\n${data.summary.healthy_platforms}/${data.summary.total_platforms} platforms healthy`);
                await this.refreshIntegrations();
                
            } catch (error) {
                console.error('Failed to run health check:', error);
                alert('Failed to run health check: ' + error.message);
            }
        },

        async exportActivityLogs() {
            try {
                const response = await fetch('/api/integrations/activity/export?hours=24&format_type=json');
                const data = await response.json();
                
                alert(`Activity logs exported to: ${data.export_path}`);
                
            } catch (error) {
                console.error('Failed to export activity logs:', error);
                alert('Failed to export activity logs: ' + error.message);
            }
        },

        async initializeAllIntegrations() {
            try {
                const response = await fetch('/api/integrations/initialize', {
                    method: 'POST'
                });
                const data = await response.json();
                
                alert(`Integrations initialized: ${data.initialized_services.join(', ')}`);
                await this.refreshIntegrations();
                
            } catch (error) {
                console.error('Failed to initialize integrations:', error);
                alert('Failed to initialize integrations: ' + error.message);
            }
        },

        async togglePlatform(platformKey, platform) {
            try {
                const endpoint = platform.enabled 
                    ? `/api/integrations/${platformKey}/disable`
                    : `/api/integrations/${platformKey}/enable`;
                
                const response = await fetch(endpoint, { method: 'POST' });
                const data = await response.json();
                
                if (data.status) {
                    await this.refreshIntegrations();
                }
                
            } catch (error) {
                console.error('Failed to toggle platform:', error);
                alert('Failed to toggle platform: ' + error.message);
            }
        },

        configurePlatform(platformKey) {
            this.selectedPlatform = platformKey;
            const platform = this.integrations[platformKey];
            
            // Reset form
            this.platformConfig = {
                api_key: '',
                enabled: platform?.enabled || false,
                shop_id: '',
                base_url: ''
            };
            
            this.showPlatformConfig = true;
        },

        async savePlatformConfig() {
            try {
                const config = {
                    platform: this.selectedPlatform,
                    api_key: this.platformConfig.api_key,
                    enabled: this.platformConfig.enabled,
                    additional_config: {}
                };
                
                // Add platform-specific config
                if (this.needsShopId(this.selectedPlatform) && this.platformConfig.shop_id) {
                    config.additional_config.shop_id = parseInt(this.platformConfig.shop_id);
                }
                
                if (this.needsBaseUrl(this.selectedPlatform) && this.platformConfig.base_url) {
                    config.additional_config.base_url = this.platformConfig.base_url;
                }
                
                const response = await fetch(`/api/integrations/${this.selectedPlatform}/configure`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const data = await response.json();
                
                if (data.status === 'configured') {
                    alert('Platform configured successfully!');
                    this.showPlatformConfig = false;
                    await this.refreshIntegrations();
                } else {
                    alert('Failed to configure platform');
                }
                
            } catch (error) {
                console.error('Failed to save platform config:', error);
                alert('Failed to save configuration: ' + error.message);
            }
        },

        async checkPlatformHealth(platformKey) {
            try {
                const response = await fetch(`/api/integrations/${platformKey}/health`);
                const data = await response.json();
                
                const health = data.health;
                alert(`${platformKey.toUpperCase()} Health:\nStatus: ${health.status}\nMessage: ${health.message}`);
                
            } catch (error) {
                console.error('Failed to check platform health:', error);
                alert('Failed to check platform health: ' + error.message);
            }
        },

        // UI Helper Methods
        getPlatformIcon(platform) {
            const icons = {
                dropbox: 'fab fa-dropbox',
                airtable: 'fas fa-table',
                etsy: 'fab fa-etsy',
                printify: 'fas fa-print',
                n8n: 'fas fa-sitemap',
                shopify: 'fab fa-shopify',
                notion: 'fas fa-sticky-note',
                canva: 'fas fa-palette',
                figma: 'fab fa-figma',
                desktop: 'fas fa-desktop',
                browser: 'fas fa-globe',
                email: 'fas fa-envelope'
            };
            return icons[platform] || 'fas fa-cube';
        },

        getPlatformIconBg(platform) {
            const colors = {
                dropbox: 'bg-blue-500',
                airtable: 'bg-orange-500',
                etsy: 'bg-orange-600',
                printify: 'bg-green-500',
                n8n: 'bg-purple-500',
                shopify: 'bg-green-600',
                notion: 'bg-gray-800',
                canva: 'bg-purple-600',
                figma: 'bg-pink-500',
                desktop: 'bg-gray-600',
                browser: 'bg-blue-600',
                email: 'bg-red-500'
            };
            return colors[platform] || 'bg-gray-500';
        },

        getHealthStatusClass(status) {
            const classes = {
                healthy: 'status-online',
                unhealthy: 'status-error',
                degraded: 'status-busy',
                disabled: 'status-offline',
                not_configured: 'status-offline'
            };
            return classes[status] || 'status-offline';
        },

        needsShopId(platform) {
            return ['etsy', 'printify'].includes(platform);
        },

        needsBaseUrl(platform) {
            return ['n8n'].includes(platform);
        },

        formatDate(dateString) {
            if (!dateString) return 'Never';
            return new Date(dateString).toLocaleDateString();
        },

        // Theme Management Functions
        async loadThemes() {
            try {
                const response = await fetch('/api/themes');
                this.availableThemes = await response.json();
                
                // Load current theme
                const currentResponse = await fetch('/api/themes/current');
                const currentTheme = await currentResponse.json();
                this.customTheme = { ...currentTheme };
                
                // Find which preset matches current theme
                for (const [key, theme] of Object.entries(this.availableThemes)) {
                    if (JSON.stringify(theme) === JSON.stringify(currentTheme)) {
                        this.selectedTheme = key;
                        break;
                    }
                }
            } catch (error) {
                console.error('Failed to load themes:', error);
            }
        },

        selectTheme(key, theme) {
            this.selectedTheme = key;
            this.customTheme = { ...theme };
        },

        async uploadLogo(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/themes/upload-logo', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    this.customTheme.logo_url = result.logo_url;
                } else {
                    alert('Failed to upload logo: ' + result.message);
                }
            } catch (error) {
                console.error('Logo upload failed:', error);
                alert('Failed to upload logo');
            }
        },

        removeLogo() {
            this.customTheme.logo_url = null;
        },

        async applyTheme() {
            try {
                const response = await fetch('/api/themes/apply', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.customTheme)
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    // Reload the theme CSS
                    const themeCss = document.getElementById('user-theme-css');
                    if (themeCss) {
                        themeCss.href = `/static/user_theme.css?v=${Date.now()}`;
                    }
                    alert('Theme applied successfully! The page will refresh.');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    alert('Failed to apply theme: ' + result.message);
                }
            } catch (error) {
                console.error('Failed to apply theme:', error);
                alert('Failed to apply theme');
            }
        },

        previewTheme() {
            // Apply theme temporarily without saving
            const root = document.documentElement;
            root.style.setProperty('--primary-color', this.customTheme.primary_color);
            root.style.setProperty('--secondary-color', this.customTheme.secondary_color);
            root.style.setProperty('--accent-color', this.customTheme.accent_color);
            root.style.setProperty('--background-color', this.customTheme.background_color);
            root.style.setProperty('--text-color', this.customTheme.text_color);
            root.style.setProperty('--font-family', this.customTheme.font_family);
            
            document.body.style.fontFamily = this.customTheme.font_family;
            document.body.style.backgroundColor = this.customTheme.background_color;
            document.body.style.color = this.customTheme.text_color;
            
            alert('Preview applied! Use "Apply Theme" to save permanently.');
        },

        async resetToDefault() {
            const defaultTheme = this.availableThemes.default;
            if (defaultTheme) {
                this.customTheme = { ...defaultTheme };
                this.selectedTheme = 'default';
                await this.applyTheme();
            }
        }
    };
}
