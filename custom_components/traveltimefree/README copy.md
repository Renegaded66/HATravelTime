# **Google Maps Travel Time**

\[\]\[releases\]  
\[\]\[license\]  
This custom Home Assistant integration and companion Add-on utilize Google Maps to retrieve the current travel time between two defined locations upon request. This allows users to create automations based on real-time traffic conditions without relying on continuously updating sensors.

## **🚀 Features**

* **On-Demand Travel Time:** Calculation is triggered by a button entity, preventing constant resource usage.  
* **Real-Time Data:** Fetches the current travel time from Google Maps using a Playwright-based backend.  
* **Modular Architecture:** Uses a dedicated **Add-on** to encapsulate the necessary web-scraping libraries (Playwright/Firefox), ensuring the core Home Assistant system remains clean and stable.  
* **Status Tracking:** Provides a last\_updated sensor entity to monitor the timestamp of the last successful or failed request.

## **💾 Installation**

The **HATravelTime** solution consists of two components that must both be installed:

1. **The Integration:** The main HACS component that provides the user interface (config flow, button, and sensor entities).  
2. **The Add-on:** The backend running the Python/Playwright libraries for web scraping.

### **A. Integration Installation (via HACS)**

The easiest way to install the integration is via **HACS** (Home Assistant Community Store).

| Repository URL (for custom repositories) |
| :---- |
| https://github.com/Renegaded66/HATravelTime.git |

To install the integration:

1. Open **HACS** in your Home Assistant frontend.  
2. Click the **three dots menu** (⋮) in the top right corner.  
3. Select **"Custom repositories"**.  
4. Paste the URL (https://github.com/Renegaded66/HATravelTime.git) into the Repository field.  
5. Select **"Integration"** as the Category.  
6. Click **"Add"**.  
7. Find the newly added **Google Maps Travel Time** integration and click **"Download"**.  
8. **Restart Home Assistant** after the download is complete.

### **B. Add-on Installation (Required Backend)**

The Add-on is **mandatory** because the required scraping libraries (like Playwright and Firefox) cannot run within a standard Home Assistant integration.

1. Go to the **Add-on Store** in Home Assistant.  
2. Click the **three dots menu** (⋮) in the top right corner.  
3. Select **"Repositories"** (Custom repositories).  
4. Paste the same URL (https://github.com/Renegaded66/HATravelTime.git) into the Repository field.  
5. Click **"Add"**.  
6. Find the new **Google Maps Travel Time Add-on** in the store.  
7. Click **"Install"**. The installation may take a few seconds, as large libraries (like the Firefox browser runtime) need to be downloaded.  
8. Once installed, there is **nothing to configure**. Simply click **"Start"**.  
9. Verify in the Add-on Logs that you see a message similar to **"Starting Travel Time"** (or similar log indicating the service is running).

## **🛠️ Integration Configuration & Usage**

Once both the Integration and the Add-on are running, you can configure your travel paths.

### **Configuration**

You can configure any number of desired trips. For each trip, you define:

1. **A Name:** A unique identifier (e.g., "Commute to Work", "Drive to Grandma").  
2. **A Start Point (Source):** The starting address or location.  
3. **A Destination Point (Target):** The ending address or location.

### **Usage**

To request the current travel time, use the **Button Entity** provided by the integration:

1. For the configured trip (e.g., "Commute to Work"), the integration creates a **Button Entity** (e.g., button.commute\_to\_work\_calculate).  
2. When you want to know the travel time (e.g., triggered by a time automation or a dashboard click), you **"press"** this button entity.  
3. This action sends a request to the running Add-on backend.  
4. The Add-on calculates the current travel time via Google Maps.  
5. The result is returned to the Integration and is displayed in the corresponding **Sensor Entity** (e.g., sensor.commute\_to\_work\_travel\_time).

The Integration also provides a **Last Updated Entity** (e.g., sensor.commute\_to\_work\_last\_updated), which is set to the current time whenever a request is successfully or unsuccessfully returned from the Add-on. This helps you monitor the status of your travel time calculations.  
\[\]: \#  
\[releases\]: https://www.google.com/search?q=https://github.com/Renegaded66/HATravelTime/releases  
\[\]: \#  
\[license\]: https://www.google.com/search?q=https://github.com/Renegaded66/HATravelTime/blob/main/LICENSE