"""
MockTopus Bot - Image Processing and Mockup Generation
Generates product mockups from design files using Photopea API
"""

import os
import json
import time
import requests
from typing import Dict, Any
from pathlib import Path
import sys

# Add shared interface to path
sys.path.append('/app/shared/bot-interface')

from bot_interface import BotInterface, BotConfig, Task, TaskResult, create_bot_config

class MockTopusBot(BotInterface):
    """Bot for generating product mockups from design files"""
    
    def __init__(self, config: BotConfig):
        super().__init__(config)
        self.photopea_api_url = os.getenv('PHOTOPEA_API_URL', 'https://www.photopea.com/api')
        self.mockup_templates = {
            't-shirt': {
                'template_url': 'https://cdn.example.com/templates/tshirt.psd',
                'placement_area': {'x': 100, 'y': 150, 'width': 200, 'height': 250}
            },
            'hoodie': {
                'template_url': 'https://cdn.example.com/templates/hoodie.psd',
                'placement_area': {'x': 80, 'y': 120, 'width': 240, 'height': 280}
            },
            'tank-top': {
                'template_url': 'https://cdn.example.com/templates/tanktop.psd',
                'placement_area': {'x': 120, 'y': 100, 'width': 160, 'height': 200}
            }
        }
    
    def process_task(self, task: Task) -> TaskResult:
        """Process mockup generation task"""
        try:
            input_data = task.input_data
            
            # Extract input parameters
            source_file_url = input_data.get('source_file')
            product_name = input_data.get('product_name', 'Product')
            target_templates = input_data.get('templates', ['t-shirt'])
            
            if not source_file_url:
                raise ValueError("No source file URL provided")
            
            self.logger.info(f"Generating mockups for {product_name}")
            
            # Generate mockups for each template
            mockups = []
            for template_name in target_templates:
                if template_name in self.mockup_templates:
                    mockup = self._generate_mockup(
                        source_file_url,
                        template_name,
                        product_name
                    )
                    mockups.append(mockup)
                else:
                    self.logger.warning(f"Unknown template: {template_name}")
            
            # Calculate confidence based on successful mockups
            confidence = len(mockups) / len(target_templates) if target_templates else 0
            
            return TaskResult(
                task_id=task.task_id,
                pipeline_id=task.pipeline_id,
                bot_id=self.config.bot_id,
                status='completed',
                output_data={
                    'input': input_data,
                    'mockups': mockups,
                    'product_name': product_name,
                    'templates_used': target_templates,
                    'total_mockups': len(mockups)
                },
                confidence=confidence,
                metadata={
                    'bot_version': '1.0.0',
                    'processing_method': 'photopea_api',
                    'templates_available': list(self.mockup_templates.keys())
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing mockup task: {e}")
            return TaskResult(
                task_id=task.task_id,
                pipeline_id=task.pipeline_id,
                bot_id=self.config.bot_id,
                status='failed',
                output_data={'input': task.input_data},
                error_message=str(e),
                confidence=0.0
            )
    
    def _generate_mockup(self, source_file_url: str, template_name: str, product_name: str) -> Dict[str, Any]:
        """Generate a single mockup using Photopea API"""
        try:
            template_config = self.mockup_templates[template_name]
            
            # In a real implementation, this would call the Photopea API
            # For now, we'll simulate the process
            
            self.logger.info(f"Generating {template_name} mockup for {product_name}")
            
            # Simulate API call delay
            time.sleep(2)
            
            # Generate mockup URL (in real implementation, this would be the actual result)
            mockup_url = f"https://cdn.example.com/mockups/{product_name.lower().replace(' ', '_')}_{template_name}_{int(time.time())}.jpg"
            
            # Simulate confidence based on template complexity
            confidence_scores = {
                't-shirt': 0.95,
                'hoodie': 0.90,
                'tank-top': 0.98
            }
            
            mockup = {
                'template': template_name,
                'image_url': mockup_url,
                'confidence': confidence_scores.get(template_name, 0.85),
                'placement_area': template_config['placement_area'],
                'generated_at': time.time(),
                'file_size': 1024 * 1024,  # 1MB simulated
                'dimensions': {'width': 800, 'height': 1000}
            }
            
            self.logger.info(f"Generated {template_name} mockup: {mockup_url}")
            return mockup
            
        except Exception as e:
            self.logger.error(f"Error generating {template_name} mockup: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Extended health check for MockTopus"""
        base_health = super().health_check()
        
        # Check Photopea API availability
        try:
            response = requests.get(f"{self.photopea_api_url}/health", timeout=5)
            photopea_status = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            photopea_status = "unreachable"
        
        base_health.update({
            'photopea_api_status': photopea_status,
            'templates_available': len(self.mockup_templates),
            'supported_templates': list(self.mockup_templates.keys())
        })
        
        return base_health

def main():
    """Main entry point for MockTopus bot"""
    config = create_bot_config('mocktopus', 'mockup_generation')
    bot = MockTopusBot(config)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("MockTopus bot stopped by user")
    except Exception as e:
        print(f"MockTopus bot error: {e}")

if __name__ == "__main__":
    main()
