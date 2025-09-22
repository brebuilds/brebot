"""
Main entry point for Brebot - Autonomous AI Agent System
Orchestrates the entire system and provides CLI interface.
"""

import argparse
import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Add src to Python path
sys.path.append(str(Path(__file__).parent))

from config import settings, load_settings
from brebot_crew import BrebotCrew
from utils import brebot_logger


class BrebotCLI:
    """Command-line interface for Brebot."""
    
    def __init__(self):
        """Initialize the Brebot CLI."""
        self.crew: Optional[BrebotCrew] = None
        self.setup_logging()
    
    def setup_logging(self):
        """Set up logging for the CLI."""
        brebot_logger.log_crew_activity(
            crew_name="BrebotCLI",
            activity="initialized",
            details={"version": "1.0.0"}
        )
    
    def initialize_crew(self) -> bool:
        """
        Initialize the Brebot crew.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            brebot_logger.log_crew_activity(
                crew_name="BrebotCLI",
                activity="initializing_crew"
            )
            
            self.crew = BrebotCrew()
            
            brebot_logger.log_crew_activity(
                crew_name="BrebotCLI",
                activity="crew_initialized",
                details={"success": True}
            )
            
            return True
            
        except Exception as e:
            brebot_logger.log_error(
                error=e,
                context="BrebotCLI.initialize_crew"
            )
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the system.
        
        Returns:
            dict: Health check results
        """
        if not self.crew:
            return {
                "status": "error",
                "message": "Crew not initialized"
            }
        
        return self.crew.health_check()
    
    def organize_files(self, directory_path: str, organization_type: str = "by_extension") -> str:
        """
        Organize files in a directory.
        
        Args:
            directory_path: Path to the directory to organize
            organization_type: Type of organization to perform
            
        Returns:
            str: Result of the organization
        """
        if not self.crew:
            return "Error: Crew not initialized. Run 'brebot init' first."
        
        return self.crew.organize_files(directory_path, organization_type)
    
    def create_folder_structure(self, base_path: str, structure_description: str) -> str:
        """
        Create a folder structure.
        
        Args:
            base_path: Base path where to create the structure
            structure_description: Description of the desired structure
            
        Returns:
            str: Result of the folder creation
        """
        if not self.crew:
            return "Error: Crew not initialized. Run 'brebot init' first."
        
        return self.crew.create_folder_structure(base_path, structure_description)
    
    def move_files(self, source_path: str, destination_base: str) -> str:
        """
        Move files to an organized structure.
        
        Args:
            source_path: Path to source files
            destination_base: Base path for organized destination
            
        Returns:
            str: Result of the file moving
        """
        if not self.crew:
            return "Error: Crew not initialized. Run 'brebot init' first."
        
        return self.crew.move_files_to_organized_structure(source_path, destination_base)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get system status.
        
        Returns:
            dict: System status information
        """
        if not self.crew:
            return {
                "status": "not_initialized",
                "message": "Crew not initialized"
            }
        
        return self.crew.get_agent_status()


def main():
    """Main entry point for the Brebot CLI."""
    parser = argparse.ArgumentParser(
        description="Brebot - Autonomous AI Agent System for Marketing & Web Design",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  brebot init                    # Initialize the system
  brebot health                  # Check system health
  brebot organize /path/to/files # Organize files by extension
  brebot create-structure /path "Projects/2024/Client_A" # Create folder structure
  brebot move /source /dest      # Move files to organized structure
  brebot status                  # Get system status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Initialize command
    init_parser = subparsers.add_parser('init', help='Initialize the Brebot system')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check system health')
    
    # Organize files command
    organize_parser = subparsers.add_parser('organize', help='Organize files in a directory')
    organize_parser.add_argument('directory', help='Directory path to organize')
    organize_parser.add_argument(
        '--type', 
        choices=['by_extension', 'by_date', 'by_project'],
        default='by_extension',
        help='Organization type (default: by_extension)'
    )
    
    # Create folder structure command
    create_parser = subparsers.add_parser('create-structure', help='Create a folder structure')
    create_parser.add_argument('base_path', help='Base path where to create the structure')
    create_parser.add_argument('structure', help='Structure description (e.g., "Projects/2024/Client_A")')
    
    # Move files command
    move_parser = subparsers.add_parser('move', help='Move files to organized structure')
    move_parser.add_argument('source', help='Source path')
    move_parser.add_argument('destination', help='Destination base path')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get system status')
    
    # Web interface command
    web_parser = subparsers.add_parser('web', help='Start web interface')
    web_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    web_parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = BrebotCLI()
    
    try:
        if args.command == 'init':
            print("🚀 Initializing Brebot system...")
            if cli.initialize_crew():
                print("✅ Brebot system initialized successfully!")
                print("🎉 Ready to organize your files and boost productivity!")
            else:
                print("❌ Failed to initialize Brebot system.")
                print("💡 Check your configuration and try again.")
                sys.exit(1)
        
        elif args.command == 'health':
            print("🔍 Checking system health...")
            health = cli.health_check()
            print(json.dumps(health, indent=2))
            
            if health.get('overall_status') == 'healthy':
                print("✅ System is healthy!")
            else:
                print("⚠️  System has issues. Check the details above.")
                sys.exit(1)
        
        elif args.command == 'organize':
            print(f"📁 Organizing files in: {args.directory}")
            print(f"📋 Organization type: {args.type}")
            result = cli.organize_files(args.directory, args.type)
            print("\n" + "="*50)
            print("ORGANIZATION RESULT:")
            print("="*50)
            print(result)
        
        elif args.command == 'create-structure':
            print(f"📂 Creating folder structure at: {args.base_path}")
            print(f"🏗️  Structure: {args.structure}")
            result = cli.create_folder_structure(args.base_path, args.structure)
            print("\n" + "="*50)
            print("FOLDER CREATION RESULT:")
            print("="*50)
            print(result)
        
        elif args.command == 'move':
            print(f"📦 Moving files from: {args.source}")
            print(f"🎯 Destination: {args.destination}")
            result = cli.move_files(args.source, args.destination)
            print("\n" + "="*50)
            print("FILE MOVING RESULT:")
            print("="*50)
            print(result)
        
        elif args.command == 'status':
            print("📊 Getting system status...")
            status = cli.get_status()
            print(json.dumps(status, indent=2))
        
        elif args.command == 'web':
            print(f"🌐 Starting Brebot web interface...")
            print(f"📍 Server will be available at: http://{args.host}:{args.port}")
            print("🔄 Starting web server...")
            
            import uvicorn
            from src.web.app import app
            
            uvicorn.run(
                app, 
                host=args.host, 
                port=args.port,
                log_level="info"
            )
    
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user.")
        sys.exit(0)
    
    except Exception as e:
        brebot_logger.log_error(
            error=e,
            context=f"BrebotCLI.main({args.command})"
        )
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
