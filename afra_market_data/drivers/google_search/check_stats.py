import os, sys, json
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)
from app.database import Database
print(json.dumps(Database().get_stats(), ensure_ascii=False, indent=2))
