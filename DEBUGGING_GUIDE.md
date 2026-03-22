# 🐛 Debugging Guide - AI Agent System

## Current Status
✅ **Both services running successfully**
- Backend: http://localhost:8000
- Frontend: http://localhost:3001
- WebSocket: ws://localhost:8000/ws/execute/{session_id}

---

## Common Issues & Solutions

### 1️⃣ Port Already in Use
**Error**: `[Errno 10048] error while attempting to bind on address`

**Solution**:
```powershell
# Find process using port 8000
netstat -ano | findstr ":8000"

# Kill the process by ID
taskkill /PID <PID> /F

# Or use a different port
python -m uvicorn founder_bi_agent.backend.main:app --port 8001 --host localhost
```

---

### 2️⃣ WebSocket Connection Refused (403)
**Error**: `server rejected WebSocket connection: HTTP 403`

**Causes & Solutions**:

a) **Routes not registered**
```python
# In founder_bi_agent/backend/main.py, ensure:
from founder_bi_agent.backend.api.ws import router as ws_router, session_router

app.include_router(ws_router)
app.include_router(session_router)
```

b) **Using wrong host binding**
```powershell
# Use localhost instead of 0.0.0.0
python -m uvicorn founder_bi_agent.backend.main:app --port 8000 --host localhost

# If you need 0.0.0.0, ensure no IPv6 conflicts:
python -m uvicorn founder_bi_agent.backend.main:app --port 8000 --host 0.0.0.0 --access-log
```

---

### 3️⃣ Frontend Not Connecting to Backend
**Error**: WebSocket connection fails in browser

**Solutions**:
a) Check DevTools Console (F12) for CORS errors
b) Verify backend is running: `curl http://localhost:8000/ws/health`
c) Check browser console network tab for failed connections
d) Ensure frontend URL matches backend URL

---

### 4️⃣ Module Import Errors
**Error**: `ModuleNotFoundError: No module named 'founder_bi_agent'`

**Solution**:
```powershell
# Run from project root directory (F:\PyTorch_GPU\Agentic_Monday_BI)
cd F:\PyTorch_GPU\Agentic_Monday_BI

# NOT from within founder_bi_agent directory
python -m uvicorn founder_bi_agent.backend.main:app --port 8000 --host localhost
```

---

### 5️⃣ ChromaDB Deprecation Warnings
**Error**: `DeprecationWarning: legacy embedding function config`

**Status**: ⚠️ **SAFE TO IGNORE** - This is a known issue with ChromaDB, not our code
- The application functions normally despite these warnings
- Can be suppressed by installing newer ChromaDB version if needed

---

### 6️⃣ Frontend Port Already in Use
**Error**: Vite dev server can't bind to port 3000/3001

**Solution**:
```powershell
# Vite will automatically try next available port
cd founder_bi_agent/frontend
npm run dev

# Or specify port explicitly
npm run dev -- --port 3002
```

---

### 7️⃣ Dependencies Missing
**Error**: `ModuleNotFoundError`, `No module named 'websockets'`

**Solution**:
```powershell
# Use torch_gpu Python environment (already activated)
pip install websockets redis -q

# Verify all dependencies
pip list | findstr -E "fastapi|uvicorn|websockets|langraph"
```

---

## Testing & Verification

### ✅ Test 1: Check WebSocket
```powershell
python test_ws_temp.py
```
**Expected Output**: 
```
✅ Connected successfully!
✅ Pong received successfully!
```

### ✅ Test 2: Check REST API
```powershell
python debug_endpoints.py
```
**Expected**: Health check returns `{"status": "ok", ...}`

### ✅ Test 3: Browser Connection
1. Open http://localhost:3001 in browser
2. Press F12 to open DevTools
3. Go to Network → WS tab
4. Look for WebSocket connection to `/ws/execute/...`
5. Should show Connected status

### ✅ Test 4: Node Graph Visualization
1. Open http://localhost:3001
2. Should see 16 nodes in graph UI
3. Try executing a query
4. Nodes should light up in real-time

---

## Backend Logs

### View logs for:
```powershell
# See recent output
get_terminal_output("17669bfe-29ba-4370-8e17-43d66241c96c")

# Look for:
# INFO:     Application startup complete.
# INFO:     127.0.0.1:XXXXX - "WebSocket /ws/execute/test-123" 101
#           (101 = WebSocket upgrade successful)
```

### Expected Log Entries
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

# When WebSocket connects:
INFO:     127.0.0.1:PORT - "WebSocket /ws/execute/SESSION" 101

# When message received:
DEBUG:    {"type": "ping", ...}
```

---

## Frontend Logs

### View logs:
```powershell
get_terminal_output("f0940854-1e73-4e38-8526-3cfdb306d817")
```

### Browser Console (F12 → Console)
```javascript
// Should show WebSocket connection messages:
"WebSocket connected: session-123"
"Message received: {type: 'pong', ...}"
```

---

## Performance Monitoring

### Check CPU/Memory:
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*"} | Select-Object ProcessName, PM, CPU
```

### Normal values:
- Backend: 50-150 MB memory, <5% CPU idle
- Frontend: 100-300 MB memory, <2% CPU idle

---

## Advanced Debugging

### Enable Verbose Logging
```python
# In backend/main.py add:
import logging
logging.basicConfig(level=logging.DEBUG)

# In backend/main.py routes:
logger = logging.getLogger(__name__)
logger.debug(f"Received message: {data}")
```

### Monitor Network Traffic
```powershell
# Use Wireshark or:
netstat -an | findstr ESTABLISHED

# Check specific ports:
netstat -ano | grep 8000
netstat -ano | grep 3001
```

### Test with wscat
```powershell
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/execute/test-123

# Send test message
{"type": "ping"}

# Expected response
{"type": "pong", "timestamp": "..."}
```

---

## Common Remediation Steps

### 🔧 Full Reset
```powershell
# 1. Kill all Python processes
Get-Process python | Stop-Process -Force

# 2. Kill all Node processes
Get-Process node | Stop-Process -Force

# 3. Clear any temp files
Remove-Item -Path debug_endpoints.py, test_ws_temp.py -ErrorAction SilentlyContinue

# 4. Restart services
# Backend:
python -m uvicorn founder_bi_agent.backend.main:app --port 8000 --host localhost

# Frontend (new terminal):
cd founder_bi_agent/frontend
npm run dev
```

### ✨ Clean Backend Restart
```powershell
# From project root
python -m uvicorn founder_bi_agent.backend.main:app --port 8000 --host localhost --reload
```

### ✨ Clean Frontend Restart
```powershell
cd founder_bi_agent/frontend
npm run dev
```

---

## Contact Debugging

If issues persist:

1. **Check file paths**: Ensure all imports use correct paths
2. **Check Python version**: `python --version` (should be 3.10+)
3. **Check Node version**: `node --version` (should be 18+)
4. **Check environment**: Verify torch_gpu environment is activated
5. **Check network**: Ensure localhost is accessible
6. **Check logs**: Review full terminal output for error messages

---

## Success Indicators ✅

You know everything is working when you see:
- ✅ Backend: "Application startup complete"
- ✅ Frontend: "VITE ready in XXX ms"
- ✅ WebSocket test: "Pong received successfully"
- ✅ Browser: Open http://localhost:3001 without errors
- ✅ WebSocket connection visible in DevTools Network tab
- ✅ Node graph renders correctly
