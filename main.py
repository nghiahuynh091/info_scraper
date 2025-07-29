#!/usr/bin/env python3
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from chatbot import ChatBotManager
def check_dependencies():
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("ERROR: Node.js not available")
            return False
    except Exception as e:
        print(f"ERROR: Node.js check failed: {e}")
        return False
    
    if not Path('node_modules').exists():
        print("Installing NPM dependencies...")
        try:
            result = subprocess.run(['npm', 'install'], 
                                  capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                print(f"ERROR: NPM install failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"ERROR: NPM install error: {e}")
            return False
    
    return True

def run_scraper():
    
    print("Running scraper...")
    
    try:
        result = subprocess.run(['node', 'src/scraper-cli.js'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("Scraping completed successfully")

            
            return True
        else:
            print(f"ERROR: Scraping failed with exit code {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("ERROR: Scraping timed out after 5 minutes")
        return False
    
    except Exception as e:
        print(f"ERROR: Scraper error: {e}")
        return False

def run_uploader():

    print("Running uploader...")
    
    try:
        manager = ChatBotManager()
        results = manager.update_vector_store()
                    
        print("Upload completed successfully")
        return True, results
    except Exception as e:
        print(f"ERROR: Upload failed: {e}")
        return False, None

def get_pipeline_stats():

    cache_file = Path(".bot_cache.json")
    articles_dir = Path("articles")
    
    stats = {
        "total_articles": 0,
        "local_files": 0,
        "added": 0,
        "updated": 0,
        "skipped": 0
    }
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            
            metadata = cache.get('_metadata', {})
            stats["total_articles"] = len([k for k in cache.keys() if not k.startswith('_')])

            stats["added"] = metadata.get('files_added', 0)
            stats["updated"] = metadata.get('files_updated', 0)
            stats["skipped"] = metadata.get('files_skipped', 0)
            
        except Exception as e:
            print(f"WARNING: Could not read cache stats: {e}")
    
    if articles_dir.exists():
        local_files = [f for f in articles_dir.glob("*.md") if f.name != "README.md"]
        stats["local_files"] = len(local_files)
    else:
        stats["local_files"] = 0
    
    return stats

def save_execution_report(success, start_time, stats, detailed_results=None):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        "status": "success" if success else "failed",
        "stats": stats,
        "log_counts": {
            "added": stats.get("added", 0),
            "updated": stats.get("updated", 0), 
            "skipped": stats.get("skipped", 0),
        },
        "latest_report": "reports/latest_log.json",
    }
    
    latest_report = reports_dir / "latest_log.json"
    with open(latest_report, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Save timestamped report
    timestamped_report = reports_dir / f"log_{timestamp}.json"
    with open(timestamped_report, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Log counts - Added: {report['log_counts']['added']}, Updated: {report['log_counts']['updated']}, Skipped: {report['log_counts']['skipped']}")
    print(f"Artifacts: {latest_report}")
    
    return report

def main():
    print("\n\n")
    start_time = time.time()
    success = False
    
    print("Scraper-Uploader Starting...")

    print("=" * 60)
    
    try:
        
        if not check_dependencies():
            print("ERROR: Dependency check failed")
            return False
        print()
        
        if not run_scraper():
            print("ERROR: Pipeline failed at scraper step")
            return False
        print()
        
        uploader_success, detailed_results = run_uploader()
        if not uploader_success:
            print("ERROR: Pipeline failed at uploader step")
            return False
        print()
        
        stats = get_pipeline_stats()
        
        print(f"Total articles: {stats['total_articles']}")
        print(f"Local files: {stats['local_files']}")

        print()
        
        success = True
        
    except KeyboardInterrupt:
        print("ERROR: Pipeline interrupted by user")
        success = False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        success = False
    
    finally:
        # Always save report
        stats = get_pipeline_stats()
        save_execution_report(success, start_time, stats, detailed_results)
        
        
        print("=" * 60)
        if success:
            print("PROCESS COMPLETED SUCCESSFULLY")
        else:
            print("PROCESS FAILED")
                
        return success

if __name__ == "__main__":
    # Run main pipeline
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            try:
                manager = ChatBotManager()
                manager.test_assistant()
                sys.exit(0)
            except Exception as e:
                print(f"Test failed: {e}")
                sys.exit(1)
    success = main()
    sys.exit(0 if success else 1)
