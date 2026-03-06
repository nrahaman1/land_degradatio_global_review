# Global Land Degradation Research Metadata (2000-2024)

Welcome to the **Global Land Degradation Research Metadata** repository. This project provides a synthesis and interactive visualization of the methodological archetypes and thematic areas driving global land degradation scientific research over the last two decades. 

It draws data from over 5,300 high-impact publications, utilizing natural language processing and spatial analytics to reveal the discipline's epistemological structure, specifically addressing the gap between retrospective diagnostic accounting and dynamic forecasting. 

## Dataset Overview

**Dataset Name:** Global Land Degradation Research Compendium & Geospatial Metadata
**Funding:** NSF_MSU HEGS Project #2343014 (Dr. Narcisa Pricope & Sk Nafiz Rahaman)

The `/data` folder includes:
- `countries.geojson` and `subregions.geojson`: Spatial boundaries enhanced with synthesized research metadata scores.
- `All_Years_Merged.csv`: Compendium of all papers analyzed over the time period.
- `Consolidated_Method_Prediction_Excel_Updated.xlsx`: Categorized extraction of methods (e.g., LULC, System Dynamics, Machine Learning).
- `Scopus-10-Analyze-FundingSponsor.csv`: Summary of funding countries/organizations driving the research.

## The Interactive Dashboard

This repository includes a sleek, "neon-themed" Mapbox GL JS dashboard that maps out the geographic footprint of land degradation studies against actual degradation severity.

### Features:
- **Interactive 3D Globe:** Dark-mode visualization using Mapbox GL JS.
- **Dynamic Layer Toggling:** Switch seamlessly between global country-level data and subregional hotspots.
- **Data Insights:** Hover over regions to examine thematic prioritization across geographic boundaries.

---

## 🚀 How to Publish This Dashboard to GitHub Pages

To make this dashboard publicly accessible via a live URL, follow these steps:

### Step 1: Initialize the Repository on GitHub
1. Go to your GitHub account and click **New Repository**.
2. Name it something like `Land-Degradation-Dashboard`.
3. Give it a short description and choose **Public**. 
4. Do NOT initialize with a README (this file serves that purpose). Click **Create repository**.

### Step 2: Upload Files
1. On your newly created repository page, click **"uploading an existing file"**.
2. Drag and drop all the contents of this folder (`index.html`, `style.css`, `app.js`, `README.md`, and the **entire `/data` folder**) into the browser window.
3. Click the green **Commit changes** button.

*Note: If the geojson files are too large for the web interface (GitHub has a ~25MB web limit, `countries.geojson` sits right below it), you may need to use GitHub Desktop or the command-line `git` functionality to push the files.*

### Step 3: Enable GitHub Pages
1. In your GitHub repository, click on the **Settings** tab (the gear icon near the top right).
2. On the left-hand sidebar, scroll down and click on **Pages**.
3. Under the **Build and deployment** section, look for the **Source** dropdown (which currently says "None").
4. Select the **`main`** branch and leave the folder as `/ (root)`.
5. Click **Save**.

### Step 4: Access Your Dashboard
GitHub will begin building your site. After 1-2 minutes, refresh the Pages settings screen. You should see a notification that your site is live, providing a URL (e.g., `https://[your-username].github.io/Land-Degradation-Dashboard`). Click the link to view your public neon dashboard!

---
*Created by Sk Nafiz Rahaman | Mississippi State University*
