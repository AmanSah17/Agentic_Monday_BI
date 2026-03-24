import uvicorn
import sys
import os

# Add current dir to path to find the package
sys.path.append(os.getcwd())

try:
    from founder_bi_agent.backend.main import app
    print("App imported successfully in diagnostic script.")
    uvicorn.run(app, host="127.0.0.1", port=8010, log_level="debug")
except Exception as e:
    import traceback
    print(f"DIAGNOSTIC CRASH: {e}")
    traceback.print_exc()
