from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = APP_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
DEMO_DATA_PATH = PROJECT_DIR / "demo_data" / "task_demo.json"
SUPERMAP_SERVICE_EXAMPLE_PATH = PROJECT_DIR / "config" / "supermap_services.example.json"
SUPERMAP_SERVICE_LOCAL_PATH = PROJECT_DIR / "config" / "supermap_services.local.json"
