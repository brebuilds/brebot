"""
Shared Bot Interface
Standard interface that all Brebot agents implement
"""

import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import requests
import redis
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    """Configuration for a bot"""
    bot_id: str
    bot_type: str
    queue_url: str
    airtable_token: str
    airtable_base_id: str
    health_check_interval: int = 30
    max_retries: int = 3
    retry_delay: int = 5

@dataclass
class Task:
    """Standard task structure"""
    task_id: str
    pipeline_id: str
    bot_type: str
    input_data: Dict[str, Any]
    priority: str = "normal"
    created_at: datetime = None
    retry_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class TaskResult:
    """Standard task result structure"""
    task_id: str
    pipeline_id: str
    bot_id: str
    status: str  # completed, failed, retry
    output_data: Dict[str, Any]
    error_message: Optional[str] = None
    processing_time: float = 0.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class MessageQueue:
    """Redis-based message queue for bot communication"""
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.task_queue = "bot_tasks"
        self.completed_queue = "bot_completed"
        self.failed_queue = "bot_failed"
    
    def add_task(self, task: Task) -> bool:
        """Add a task to the queue"""
        try:
            task_data = {
                'task_id': task.task_id,
                'pipeline_id': task.pipeline_id,
                'bot_type': task.bot_type,
                'input_data': task.input_data,
                'priority': task.priority,
                'created_at': task.created_at.isoformat(),
                'retry_count': task.retry_count
            }
            
            # Add to queue with priority
            priority_score = self._get_priority_score(task.priority)
            self.redis_client.zadd(
                self.task_queue,
                {json.dumps(task_data): priority_score}
            )
            
            logger.info(f"Added task {task.task_id} to queue")
            return True
        except Exception as e:
            logger.error(f"Failed to add task to queue: {e}")
            return False
    
    def get_next_task(self, bot_type: str) -> Optional[Task]:
        """Get the next task for a specific bot type"""
        try:
            # Get highest priority task for this bot type
            tasks = self.redis_client.zrevrange(self.task_queue, 0, -1)
            
            for task_json in tasks:
                task_data = json.loads(task_json)
                if task_data['bot_type'] == bot_type:
                    # Remove from queue
                    self.redis_client.zrem(self.task_queue, task_json)
                    
                    # Convert back to Task object
                    task = Task(
                        task_id=task_data['task_id'],
                        pipeline_id=task_data['pipeline_id'],
                        bot_type=task_data['bot_type'],
                        input_data=task_data['input_data'],
                        priority=task_data['priority'],
                        created_at=datetime.fromisoformat(task_data['created_at']),
                        retry_count=task_data['retry_count']
                    )
                    
                    logger.info(f"Retrieved task {task.task_id} for {bot_type}")
                    return task
            
            return None
        except Exception as e:
            logger.error(f"Failed to get next task: {e}")
            return None
    
    def complete_task(self, task_id: str, result: TaskResult) -> bool:
        """Mark a task as completed"""
        try:
            result_data = {
                'task_id': result.task_id,
                'pipeline_id': result.pipeline_id,
                'bot_id': result.bot_id,
                'status': result.status,
                'output_data': result.output_data,
                'error_message': result.error_message,
                'processing_time': result.processing_time,
                'confidence': result.confidence,
                'metadata': result.metadata,
                'completed_at': datetime.now().isoformat()
            }
            
            self.redis_client.lpush(self.completed_queue, json.dumps(result_data))
            logger.info(f"Marked task {task_id} as completed")
            return True
        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            return False
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Mark a task as failed"""
        try:
            fail_data = {
                'task_id': task_id,
                'error_message': error_message,
                'failed_at': datetime.now().isoformat()
            }
            
            self.redis_client.lpush(self.failed_queue, json.dumps(fail_data))
            logger.info(f"Marked task {task_id} as failed")
            return True
        except Exception as e:
            logger.error(f"Failed to mark task as failed: {e}")
            return False
    
    def _get_priority_score(self, priority: str) -> float:
        """Convert priority to numeric score"""
        priority_scores = {
            'low': 1.0,
            'normal': 2.0,
            'high': 3.0,
            'critical': 4.0
        }
        return priority_scores.get(priority, 2.0)

class AirtableClient:
    """Client for Airtable integration"""
    
    def __init__(self, token: str, base_id: str):
        self.token = token
        self.base_id = base_id
        self.base_url = f"https://api.airtable.com/v0/{base_id}"
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def log_bot_result(self, result: TaskResult) -> bool:
        """Log bot result to Airtable"""
        try:
            record_data = {
                'fields': {
                    'Log ID': result.task_id,
                    'Bot ID': result.bot_id,
                    'Pipeline ID': result.pipeline_id,
                    'Task Type': result.bot_id,  # Bot ID serves as task type
                    'Status': result.status,
                    'Processing Time': result.processing_time,
                    'Confidence': result.confidence,
                    'Input Data': json.dumps(result.output_data.get('input', {})),
                    'Output Data': json.dumps(result.output_data),
                    'Error Message': result.error_message or '',
                    'Metadata': json.dumps(result.metadata),
                    'Timestamp': datetime.now().isoformat()
                }
            }
            
            response = requests.post(
                f"{self.base_url}/Bot%20Logs",
                headers=self.headers,
                json=record_data
            )
            
            if response.status_code == 200:
                logger.info(f"Logged result for task {result.task_id} to Airtable")
                return True
            else:
                logger.error(f"Failed to log to Airtable: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging to Airtable: {e}")
            return False
    
    def update_pipeline_status(self, pipeline_id: str, status: str, current_step: str = None, results: Dict = None) -> bool:
        """Update pipeline status in Airtable"""
        try:
            # First, find the pipeline record
            response = requests.get(
                f"{self.base_url}/Pipelines",
                headers=self.headers,
                params={'filterByFormula': f"{{Pipeline ID}} = '{pipeline_id}'"}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to find pipeline {pipeline_id}")
                return False
            
            records = response.json().get('records', [])
            if not records:
                logger.error(f"Pipeline {pipeline_id} not found")
                return False
            
            record_id = records[0]['id']
            
            # Update the record
            update_data = {
                'fields': {
                    'Status': status,
                    'Updated At': datetime.now().isoformat()
                }
            }
            
            if current_step:
                update_data['fields']['Current Step'] = current_step
            
            if results:
                update_data['fields']['Results'] = json.dumps(results)
            
            response = requests.patch(
                f"{self.base_url}/Pipelines/{record_id}",
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code == 200:
                logger.info(f"Updated pipeline {pipeline_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update pipeline: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating pipeline status: {e}")
            return False

class BotInterface(ABC):
    """Abstract base class for all Brebot agents"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.queue = MessageQueue(config.queue_url)
        self.airtable = AirtableClient(config.airtable_token, config.airtable_base_id)
        self.logger = logging.getLogger(f"bot.{config.bot_id}")
        self.running = False
    
    @abstractmethod
    def process_task(self, task: Task) -> TaskResult:
        """Process a task - must be implemented by each bot"""
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the bot"""
        return {
            'bot_id': self.config.bot_id,
            'bot_type': self.config.bot_type,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': time.time() - getattr(self, 'start_time', time.time())
        }
    
    def run(self):
        """Main bot execution loop"""
        self.start_time = time.time()
        self.running = True
        self.logger.info(f"Starting bot {self.config.bot_id}")
        
        while self.running:
            try:
                # Get next task
                task = self.queue.get_next_task(self.config.bot_type)
                
                if task:
                    self.logger.info(f"Processing task {task.task_id}")
                    start_time = time.time()
                    
                    try:
                        # Process the task
                        result = self.process_task(task)
                        result.processing_time = time.time() - start_time
                        
                        # Complete the task
                        self.queue.complete_task(task.task_id, result)
                        
                        # Log to Airtable
                        self.airtable.log_bot_result(result)
                        
                        # Update pipeline status if needed
                        if result.status == 'completed':
                            self.airtable.update_pipeline_status(
                                result.pipeline_id,
                                'in_progress',
                                self.config.bot_type,
                                result.output_data
                            )
                        
                        self.logger.info(f"Completed task {task.task_id} in {result.processing_time:.2f}s")
                        
                    except Exception as e:
                        self.logger.error(f"Error processing task {task.task_id}: {e}")
                        
                        # Create failure result
                        result = TaskResult(
                            task_id=task.task_id,
                            pipeline_id=task.pipeline_id,
                            bot_id=self.config.bot_id,
                            status='failed',
                            output_data={},
                            error_message=str(e),
                            processing_time=time.time() - start_time
                        )
                        
                        self.queue.fail_task(task.task_id, str(e))
                        self.airtable.log_bot_result(result)
                
                else:
                    # No tasks available, wait a bit
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal")
                self.running = False
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in bot loop: {e}")
                time.sleep(5)  # Wait before retrying
        
        self.logger.info(f"Bot {self.config.bot_id} stopped")

def create_bot_config(bot_id: str, bot_type: str) -> BotConfig:
    """Create bot configuration from environment variables"""
    import os
    
    return BotConfig(
        bot_id=bot_id,
        bot_type=bot_type,
        queue_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
        airtable_token=os.getenv('AIRTABLE_TOKEN'),
        airtable_base_id=os.getenv('AIRTABLE_BASE_ID')
    )
