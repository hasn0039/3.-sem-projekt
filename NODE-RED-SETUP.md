# Node-RED Complete Setup Guide for Liquid Dispensation System

This guide will walk you through installing Node-RED and setting up your liquid dispensation system dashboard step by step.

---

## Prerequisites

- Raspberry Pi with Raspbian OS (or any Linux system)
- Internet connection
- The `node-red-complete-flow.json` file from this project
- SSH access or direct terminal access to the Pi

---

## Step 1: Update Your System

First, update the package manager to ensure you have the latest software versions:

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

This ensures all packages are current before installation.

---

## Step 2: Install Node.js and npm

Node-RED requires Node.js and npm (Node Package Manager):

```bash
sudo apt-get install -y nodejs npm
```

Verify installation:
```bash
node --version
npm --version
```

Both should display version numbers.

---

## Step 3: Install Node-RED

Install Node-RED globally:

```bash
sudo npm install -g node-red
```

This may take 5-10 minutes. Once complete, you can start Node-RED with:

```bash
node-red
```

You should see output like:
```
Welcome to Node-RED
...
[info] Server now running at http://127.0.0.1:1880/
```

**Don't close this terminal yet.** Open a new terminal window and continue with the next steps.

---

## Step 4: Install Required Dashboard Package

Open a new terminal window (keep Node-RED running in the first):

```bash
cd ~/.node-red
npm install node-red-dashboard
```

This installs the dashboard UI components. Wait for installation to complete (2-5 minutes).

---

## Step 5: Install MQTT Broker (Mosquitto)

In the new terminal, install Mosquitto (the MQTT message broker):

```bash
sudo apt-get install -y mosquitto mosquitto-clients
```

Start the MQTT broker:

```bash
sudo systemctl start mosquitto
```

Enable it to start automatically on boot:

```bash
sudo systemctl enable mosquitto
```

Verify it's running:

```bash
sudo systemctl status mosquitto
```

You should see `Active: active (running)`. Press `Q` to exit.

---

## Step 6: Restart Node-RED

Go back to the terminal running Node-RED and stop it:

```
Press Ctrl+C
```

Wait for it to shut down cleanly.

Restart Node-RED:

```bash
node-red
```

You should see it running again at `http://127.0.0.1:1880/`

---

## Step 7: Access Node-RED Web Interface

Open a web browser and go to:

```
http://localhost:1880
```

Or if accessing from a different computer:

```
http://<raspberry-pi-ip>:1880
```

You should see the Node-RED editor with a blank canvas on the left and a palette of available nodes on the right.

---

## Step 8: Import the Flow

Now you'll import the dashboard configuration:

### Method 1: From File (Recommended)

1. Click the **Menu** button (three horizontal lines) in the top-right corner
2. Select **Import**
3. Click **select a file to import**
4. Navigate to and select `node-red-complete-flow.json`
5. Click the **Import** button in the dialog
6. You'll see a confirmation - click **Import** again

### Method 2: Copy-Paste

1. Click **Menu** → **Import**
2. Open `node-red-complete-flow.json` in a text editor
3. Copy all the JSON content
4. In the Node-RED import dialog, paste the JSON into the text area
5. Click **Import**

---

## Step 9: Review and Configure the Imported Flow

After importing, you should see:

- **Two tabs** at the top: "Liquid Control" and "Monitoring"
- Various colored nodes connected together
- Two configuration nodes at the bottom (this is normal)

### Important: Configure MQTT Broker Connection

1. Look for the **MQTT Broker node** (appears as a red circle with text)
2. Double-click on it to open its configuration
3. Verify the **Server** field shows:
   - If Node-RED and Pi are on same machine: `localhost`
   - If accessing from network: Your Raspberry Pi's IP address (e.g., `192.168.1.100`)
4. Keep **Port** as `1883`
5. Click **Update**

---

## Step 10: Deploy the Flow

1. Click the red **Deploy** button in the top-right corner
2. Wait for the message "Deployed successfully" at the top
3. You should see green circles under the MQTT nodes (connected)

If you see red circles or errors:
- Check MQTT broker is running: `sudo systemctl status mosquitto`
- Verify MQTT broker IP in the configuration
- Check Node-RED debug console (right panel)

---

## Step 11: Access Your Dashboard

Once deployed, access the dashboard at:

```
http://localhost:1880/ui
```

Or from another computer:

```
http://<raspberry-pi-ip>:1880/ui
```

You should see two tabs:
- **Liquid Control** - For sending dispensing commands
- **Monitoring** - For viewing live sensor data and charts

---

## Step 12: Verify Connection to Raspberry Pi

Before running your Python script, test the MQTT connection:

```bash
mosquitto_pub -t liquid_system/level -m 2500
```

In the Node-RED dashboard, the water level gauge should immediately update to 2500. This confirms MQTT is working.

---

## Step 13: Run Your Python Script on Raspberry Pi

Copy your `main.py` script to the Raspberry Pi:

```bash
scp main.py pi@<raspberry-pi-ip>:~/khelp/main.py
```

SSH into the Pi:

```bash
ssh pi@<raspberry-pi-ip>
```

Navigate to the script directory and run it:

```bash
cd ~/khelp
python3 main.py
```

You should see:
```
============================================================
Initializing Liquid Dispensation System
============================================================
...
All components initialized successfully!
```

---

## Step 14: Test the System

Your dashboard is now live! Test it:

1. **In the Node-RED dashboard:**
   - Click a quick button (e.g., "5ml Push")
   - Watch the water level gauge update
   - Watch the status panel show dispensing results

2. **Check the Python script output:**
   - It should log each command received
   - Display sensor readings

3. **Monitor charts:**
   - Go to the "Monitoring" tab
   - Charts will fill in as data is collected
   - Charts show the last hour of history

---

## Running Node-RED in Background (Optional)

To run Node-RED automatically, you can use `pm2`:

```bash
sudo npm install -g pm2
pm2 start `which node-red` -- --max-old-space-size=256
pm2 save
pm2 startup
```

Then Node-RED will start automatically when your Raspberry Pi boots.

---

## Dashboard Overview

### Liquid Control Tab
- **Custom Dispense Form** - Enter exact ml amount and direction (push/pull)
- **Quick Buttons** - 5ml and 10ml push buttons for fast dispensing

### Monitoring Tab
- **Water Level Gauge** - Real-time ADC reading (0-4095)
  - Blue (0-1365): Low level
  - Orange (1365-2730): Medium level
  - Red (2730-4095): High level

- **Temperature Gauge** - Real-time temperature (0-50°C)
  - Green (0-20°C): Cool
  - Orange (20-35°C): Normal
  - Red (35-50°C): Hot

- **Charts** - Historical data over the last hour
  - Water level trend
  - Temperature trend

- **Status Display** - Last dispensing operation details
  - Volume dispensed
  - Water levels before/after
  - Displacement measured

---

## Troubleshooting

### Node-RED Won't Start
```bash
# Check if port 1880 is already in use
sudo lsof -i :1880
# Kill the process if needed
sudo kill -9 <PID>
```

### MQTT Connection Failed
```bash
# Verify MQTT is running
sudo systemctl status mosquitto

# Restart MQTT if needed
sudo systemctl restart mosquitto

# Test MQTT connection
mosquitto_sub -t liquid_system/level
# In another terminal:
mosquitto_pub -t liquid_system/level -m 1500
```

### Dashboard Not Loading
1. Ensure `node-red-dashboard` is installed:
   ```bash
   npm list -g node-red-dashboard
   ```
2. Restart Node-RED:
   ```bash
   Press Ctrl+C, then run: node-red
   ```
3. Clear browser cache (Ctrl+Shift+Del)
4. Try accessing from a different browser

### Python Script Not Communicating
1. Verify MQTT broker IP matches in `main.py`
2. Test MQTT manually:
   ```bash
   mosquitto_pub -t liquid_system/level -m 2000
   ```
3. Check Python script output for connection errors
4. Ensure firewall allows MQTT port 1883

### No Data Appearing in Gauges
1. Check that Python script is running: `ps aux | grep main.py`
2. Verify MQTT connection in Node-RED debug (right panel)
3. Manually publish test data:
   ```bash
   mosquitto_pub -t liquid_system/level -m 2500
   mosquitto_pub -t liquid_system/temperature -m '{"sensor1": 22.5}'
   ```

---

## MQTT Topics Reference

| Topic | Purpose | Expected Data |
|-------|---------|----------------|
| `liquid_system/command` | Control stepper | `{"ml": 5, "direction": 1}` |
| `liquid_system/status` | Dispensing results | `{"ml_dispensed": 5, ...}` |
| `liquid_system/level` | Water level | `2500` (0-4095) |
| `liquid_system/temperature` | Temperature reading | `{"sensor1": 22.5}` |

---

## Next Steps

1. **Customize thresholds** - Edit gauge warning levels in Node-RED nodes
2. **Add alerts** - Install `node-red-contrib-slack` for notifications
3. **Add database** - Install `node-red-contrib-influxdb` to log historical data
4. **Create automations** - Add function nodes to auto-trigger at certain levels

### 5. Access Dashboard
After deployment, open: `http://localhost:1880/ui`

## Dashboard Features

### Control Panel
- **Dispense Control Form** - Input exact ml amount and direction (push/pull)
- **Quick Buttons** - 5ml, 10ml, 20ml preset buttons for fast dispensing

### Monitoring
- **Water Level Gauge** - Real-time ADC reading (0-4095)
  - Blue zone (0-1365): Low
  - Orange zone (1365-2730): Medium
  - Red zone (2730-4095): High

- **Temperature Gauge** - Real-time temperature (°C)
  - Green (0-20°C): Cool
  - Orange (20-35°C): Normal
  - Red (35-50°C): Hot

### Charts
- **Water Level Chart** - Historical water level over time (last hour)
- **Temperature Chart** - Historical temperature over time (last hour)

### Status Display
Shows last dispensing operation:
- Volume dispensed (ml)
- Water level before/after
- Actual displacement measured
- Timestamp

## MQTT Topics

| Topic | Direction | Data | Example |
|-------|-----------|------|---------|
| `liquid_system/command` | IN | JSON command | `{"ml": 5, "direction": 1}` |
| `liquid_system/status` | OUT | Dispensing results | `{"ml_dispensed": 5, "level_before": 1200, ...}` |
| `liquid_system/level` | OUT | Water level (0-4095) | `1850` |
| `liquid_system/temperature` | OUT | Temperature reading | `{"rom1": 22.5}` |

## Troubleshooting

### MQTT Connection Failed
- Check MQTT broker is running: `sudo systemctl status mosquitto`
- Verify IP address in MQTT node configuration
- Test connection: `mosquitto_sub -t "liquid_system/#"`

### No Data Appearing
- Check Raspberry Pi script is running
- Verify MQTT broker IP matches in both Node-RED and Pi script
- Check debug console (right panel in Node-RED)
- Test MQTT with: `mosquitto_pub -t liquid_system/level -m 1500`

### Dashboard Not Loading
- Ensure `node-red-dashboard` is installed
- Restart Node-RED: Ctrl+C then `node-red`
- Clear browser cache

## Customization

### Change MQTT Broker IP
1. Double-click MQTT broker node (blue ones)
2. Update "Server" field with your broker IP
3. Click **Update** and **Deploy**

### Add More Quick Buttons
1. Duplicate one of the quick buttons
2. Change label and payload (ml value)
3. Deploy

### Change Gauge Ranges
1. Edit gauge node
2. Change "Min" and "Max" values
3. Adjust segment colors as needed
4. Deploy

### Add Notifications
1. Import `node-red-contrib-slack` or similar
2. Add nodes after MQTT in nodes
3. Send alerts when level is too high/low

## Starting Everything

On Raspberry Pi:
```bash
# Terminal 1 - Start MQTT broker
sudo systemctl start mosquitto

# Terminal 2 - Start Node-RED
node-red

# Terminal 3 - Start your Python script
cd ~/khelp
python3 main.py
```

Then access dashboard at: `http://raspberrypi-ip:1880/ui`
