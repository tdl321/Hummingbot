# Hummingbot Docker Container Commands

## 🐳 Current Status

Your Hummingbot Docker container is **RUNNING**:
- Container Name: `hummingbot`
- Container ID: `3ac2400d0349`
- Status: Up 12 hours
- Image: `hummingbot-hummingbot:latest`

---

## 🚀 How to Access the Running Container

### **Option 1: Attach to Running Container** (Recommended)

```bash
docker attach hummingbot
```

**To detach without stopping:**
Press `Ctrl+P` then `Ctrl+Q`

### **Option 2: Execute Commands in Container**

```bash
# Start a new bash session in the running container
docker exec -it hummingbot bash

# Or run Hummingbot directly
docker exec -it hummingbot /home/hummingbot/miniconda3/envs/hummingbot/bin/python bin/hummingbot.py
```

### **Option 3: View Logs**

```bash
# Follow logs in real-time
docker logs -f hummingbot

# View last 50 lines
docker logs --tail 50 hummingbot

# View logs with timestamps
docker logs -t hummingbot
```

---

## 🔄 Restart the Container (Fresh Start)

### **Restart with Current Config:**

```bash
docker restart hummingbot
```

### **Stop and Start:**

```bash
# Stop
docker stop hummingbot

# Start
docker start hummingbot

# Attach
docker attach hummingbot
```

### **Complete Rebuild (if needed):**

```bash
# Stop and remove old container
docker stop hummingbot
docker rm hummingbot

# Rebuild image
docker-compose build

# Start fresh
docker-compose up -d

# Attach
docker attach hummingbot
```

---

## 📋 Test Extended Connector in Docker

### **Method 1: Quick Test (From Host)**

```bash
# Execute Python script inside container
docker exec -it hummingbot python /home/hummingbot/scripts/test_ui_keys_directly.py
```

### **Method 2: Interactive Session**

```bash
# Attach to container
docker attach hummingbot

# Inside container, run:
python scripts/test_ui_keys_directly.py
```

### **Method 3: Check Extended Config**

```bash
# View config from host
docker exec hummingbot cat /home/hummingbot/conf/connectors/extended_perpetual.yml
```

---

## 🔧 Useful Docker Commands

### **Check Container Health:**

```bash
# Container status
docker ps | grep hummingbot

# Resource usage
docker stats hummingbot --no-stream

# Inspect container
docker inspect hummingbot
```

### **Access Container Files:**

```bash
# Copy file FROM container
docker cp hummingbot:/home/hummingbot/conf/connectors/extended_perpetual.yml ./extended_config.yml

# Copy file TO container
docker cp ./new_config.yml hummingbot:/home/hummingbot/conf/connectors/extended_perpetual.yml
```

### **View Container Filesystem:**

```bash
# List files in container
docker exec hummingbot ls -la /home/hummingbot/conf/connectors/

# View logs directory
docker exec hummingbot ls -la /home/hummingbot/logs/
```

---

## 🐛 Debug Extended Connector

### **Check if Extended Connector is Loaded:**

```bash
docker exec hummingbot python -c "
from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import ExtendedPerpetualDerivative
print('✅ Extended connector loaded successfully')
"
```

### **Test API Keys in Container:**

```bash
# Interactive test
docker exec -it hummingbot python /home/hummingbot/scripts/test_ui_keys_directly.py

# Or create a quick test script
docker exec hummingbot bash -c "cd /home/hummingbot && python scripts/test_ui_keys_directly.py"
```

### **Check for 401 Errors in Logs:**

```bash
# Search logs for errors
docker exec hummingbot grep -i "401\|unauthorized" /home/hummingbot/logs/*.log

# Recent Extended errors
docker logs hummingbot 2>&1 | grep -i "extended\|401" | tail -20
```

---

## 📊 Docker Compose Commands

### **Start All Services:**

```bash
docker-compose up -d
```

### **View Compose Logs:**

```bash
docker-compose logs -f
```

### **Rebuild After Code Changes:**

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **Clean Everything:**

```bash
# Stop and remove
docker-compose down

# Remove image
docker rmi hummingbot-hummingbot

# Rebuild from scratch
docker-compose build
docker-compose up -d
```

---

## 🎯 Quick Access Commands

### **Most Common:**

```bash
# Attach to running Hummingbot
docker attach hummingbot

# Get a bash shell
docker exec -it hummingbot bash

# View live logs
docker logs -f hummingbot

# Restart
docker restart hummingbot
```

---

## 🔐 Test Extended Auth in Docker

### **Step 1: Attach to Container**

```bash
docker attach hummingbot
```

### **Step 2: Inside Container, Run Test**

```python
# At Hummingbot prompt:
exit

# Then run:
python scripts/test_ui_keys_directly.py
```

### **Step 3: Check Results**

If keys work in direct test but not in Hummingbot → Encryption/decryption issue
If keys don't work → Need fresh keys from UI

---

## 📝 Your Current Situation

Based on your Extended connector issue:

### **Recommended Test Sequence:**

```bash
# 1. Get a bash shell in container
docker exec -it hummingbot bash

# 2. Test API keys directly
cd /home/hummingbot
python scripts/test_ui_keys_directly.py

# 3. Check what's in config
cat conf/connectors/extended_perpetual.yml

# 4. Check recent errors
grep -i "401\|extended" logs/*.log | tail -20

# 5. Exit and try starting Hummingbot
exit
docker attach hummingbot
```

---

## 🚨 Important Notes

### **Detaching vs Stopping:**

- `Ctrl+C` = STOPS the container ❌
- `Ctrl+P, Ctrl+Q` = Detaches without stopping ✅
- `exit` command = Stops the container ❌

### **Config Persistence:**

Your configs are mounted from the host:
- Host: `/Users/tdl321/hummingbot/conf/`
- Container: `/home/hummingbot/conf/`

Changes to config files on host are reflected in container!

### **Logs Location:**

- Host: `/Users/tdl321/hummingbot/logs/`
- Container: `/home/hummingbot/logs/`

---

## ✅ Next Steps for Extended Testing

```bash
# 1. Access container
docker exec -it hummingbot bash

# 2. Test your Extended keys
python scripts/test_ui_keys_directly.py
# Paste your API key when prompted

# 3. Based on results:
# - If keys work → Check Hummingbot decryption
# - If keys fail → Generate fresh keys from Extended UI

# 4. Start Hummingbot
exit
docker attach hummingbot
# Inside Hummingbot: connect extended_perpetual
```

---

Choose your next action:
- **Attach to running container**: `docker attach hummingbot`
- **Get bash shell**: `docker exec -it hummingbot bash`
- **Test keys**: `docker exec -it hummingbot python scripts/test_ui_keys_directly.py`
- **View logs**: `docker logs -f hummingbot`
