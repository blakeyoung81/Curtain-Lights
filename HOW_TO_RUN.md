# 🚀 How to Run Your Gotham Lights System

## **Quick Start** (2 commands)

```bash
# 1. Start everything with one command
./start.sh

# 2. Or start manually:
# Backend: uvicorn app.main:app --reload --port 8000
# Frontend: cd frontend && npm run dev
```

## **Access Your System**
- 🎨 **Main App**: http://localhost:5173
- 📡 **API**: http://localhost:8000  
- 📚 **API Docs**: http://localhost:8000/docs

---

## ❓ **Your Questions Answered**

### **"Does this just always have to be running to get the signals?"**

**Short Answer**: No, but it depends on what you want:

#### **🏠 For Home Use (Local)**
- **Manual Control**: Just run `./start.sh` when you want to control lights
- **Automated Triggers**: Keep it running to respond to calendar events, time-based rules, etc.
- **Your Choice**: Turn it on/off as needed

#### **🌐 For Always-On Automation (Cloud)**
- **Yes, it should stay running** to:
  - Monitor your calendar for events
  - Respond to time-based triggers
  - Handle webhook notifications
  - Execute scheduled automations

### **"How does the polling work?"**

The system has **two layers**:

#### **1. 🔄 Local Polling (Your Computer)**
```python
# In app/main.py - runs while server is running
async def background_polling():
    while True:
        await check_calendar_events()
        await process_automations()
        await update_device_status()
        await asyncio.sleep(60)  # Check every minute
```

#### **2. ☁️ Cloud Polling (GitHub Actions)**
```yaml
# In .github/workflows/cron.yml - runs in the cloud
schedule:
  - cron: '* * * * *'  # Every minute, even when your computer is off
```

---

## 🏗️ **System Architecture**

### **When Running Locally**
```
You → Frontend (React) → Backend (FastAPI) → Govee Lights
                     ↓
               Background Tasks:
               • Calendar monitoring
               • Time-based triggers
               • Device status updates
```

### **When Deployed to Cloud**
```
GitHub Actions → Cloud Server → Govee Lights
      ↓              ↓
  Every minute   Background Tasks
                 + Web Interface
```

---

## 🎯 **Usage Scenarios**

### **Scenario 1: Manual Control Only**
```bash
# When you want to control lights:
./start.sh
# Use the web interface
# Stop when done: Ctrl+C
```

### **Scenario 2: Smart Home Automation**
```bash
# Always running for automation:
./start.sh
# Leave running 24/7 for:
# • Calendar-based triggers
# • Time-based scenes
# • Webhook responses
```

### **Scenario 3: Cloud Deployment**
```bash
# Deploy once, runs forever:
fly deploy
# GitHub Actions keeps it alive
# Access from anywhere
```

---

## 🔧 **Fixing GitHub Workflow Errors**

The errors you're seeing are because `FLY_APP_NAME` needs to be set as a GitHub secret:

### **To Fix:**
1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add secret: `FLY_APP_NAME` = `your-app-name`

### **Or Disable Cloud Polling:**
```bash
# Remove the workflow file if you don't need cloud polling:
rm .github/workflows/cron.yml
```

---

## 🎛️ **System Control Commands**

```bash
# Start everything
./start.sh

# Start backend only
uvicorn app.main:app --reload --port 8000

# Start frontend only
cd frontend && npm run dev

# Stop everything
# Ctrl+C (if using start.sh)
# Or kill processes manually:
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9

# Check if running
curl http://localhost:8000/
curl http://localhost:5173/
```

---

## 🔍 **What Happens When Running**

### **Backend Tasks** (localhost:8000)
- ✅ User authentication & session management
- ✅ Device discovery & control
- ✅ Calendar event monitoring
- ✅ Automation rule processing
- ✅ OAuth integration handling
- ✅ Background polling every 60 seconds

### **Frontend Interface** (localhost:5173)
- ✅ Beautiful authentication system
- ✅ Real-time device control
- ✅ Settings management
- ✅ OAuth connection status
- ✅ Live system status updates

### **Cloud Polling** (GitHub Actions)
- ✅ Keeps cloud deployment alive
- ✅ Ensures continuous operation
- ✅ Calls `/cron` endpoint every minute
- ⚠️ Only needed for cloud deployment

---

## 💡 **Recommendations**

### **For Testing & Development**
```bash
./start.sh  # Start when needed, stop when done
```

### **For Daily Use**
```bash
./start.sh  # Keep running for smart automations
```

### **For Production**
```bash
fly deploy  # Deploy to cloud for 24/7 operation
```

---

## 🚨 **Troubleshooting**

### **Ports Already in Use**
```bash
# The start.sh script handles this automatically, or manually:
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

### **Missing Dependencies**
```bash
# Backend:
pip install -r requirements.txt

# Frontend:
cd frontend && npm install
```

### **Authentication Issues**
- Check `.env` file has `JWT_SECRET_KEY`
- Verify API endpoints are accessible
- Clear browser localStorage if needed

---

**🎉 Ready to control your lights like Batman!** 