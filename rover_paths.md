# **Technical Specification: Hover-Activated Historical Traverse Paths and EDL Coverage Zones**

**Project:** Mars 3D Planetary Explorer (MALO_MARS_HiRes_Render)  
**Target Platform:** WebGL / Three.js / Canvas 2D / Antigravity CLI  
**Document Class:** System Architecture & Spatial Telemetry Specification  

---

## **1. System Overview & Objective**
Interactive planetary visualization systems require distinct visual treatments for mobile robotic rovers versus stationary landed platforms. The objective of this feature is to implement real-time, hover-activated 3D spatial geometry overlays when users interact with completed mission entries in the application interface or hover over mission beacons on the 3D globe. 

* **Mobile Rovers:** Render 3D line string geometry representing the cumulative drive traverse path from touchdown to mission conclusion. 
* **Stationary Landers:** Render 3D surface polygons and boundary rings representing the Entry, Descent, and Landing (EDL) target ellipse or localized instrument workspace footprint. 

---

## **2. Spatial Classification of Completed Missions**
Completed missions are partitioned into two operational archetypes based on surface mobility: 

### **2.1 Mobile Rovers (Traverse Line Strings)**
* **Opportunity (MER-B):** $45.16 \text{ km}$ traverse across Meridiani Planum from Eagle Crater to Endeavour Crater. 
* **Spirit (MER-A):** $7.73 \text{ km}$ traverse through Gusev Crater and the Columbia Hills. 
* **Zhurong (Tianwen-1):** $1.92 \text{ km}$ southward traverse across Southern Utopia Planitia. 
* **Sojourner (Mars Pathfinder):** $\sim 100 \text{ m}$ micro-traverse around Carl Sagan Memorial Station in Ares Vallis. 

### **2.2 Stationary Landers (EDL Ellipses & Workspace Rings)**
* **InSight Lander:** $130 \text{ km} \times 27 \text{ km}$ targeted EDL ellipse in Elysium Planitia, alongside a $3 \text{ m}$ radius workspace ring for the SEIS seismometer and HP3 heat probe. 
* **Phoenix Lander:** $100 \text{ km} \times 20 \text{ km}$ landing ellipse in Green Valley, Vastitas Borealis. 
* **Viking 1 & Viking 2:** Historical $280 \text{ km} \times 100 \text{ km}$ landing ellipses in Chryse Planitia and Utopia Planitia. 

---

## **3. Mathematical Foundations & Coordinate Reference System (CRS)**

### **3.1 Geodetic Coordinate Reference Frame**
Spatial positioning references the Mars 2000 / IAU 2000 coordinate frame with planetocentric East-positive longitudes $\phi \in [0^\circ, 360^\circ]$ and planetocentric latitudes $\psi \in [-90^\circ, +90^\circ]$ relative to the MOLA areoid datum (610.5 Pa equipotential surface). 

### **3.2 Conversion from Geodetic to 3D Cartesian Coordinates**
To map planetocentric coordinates $(\phi, \psi, \text{elevation})$ to 3D WebGL camera space on a sphere with base radius $R_{\text{Mars}} = 1.0$:

$$\text{radLat} = \psi \cdot \frac{\pi}{180}$$
$$\text{radLon} = \phi \cdot \frac{\pi}{180}$$
$$r = R_{\text{Mars}} + \text{altitudeOffset}$$
$$X = r \cdot \cos(\text{radLat}) \cdot \cos(\text{radLon})$$
$$Y = r \cdot \sin(\text{radLat})$$
$$Z = -r \cdot \cos(\text{radLat}) \cdot \sin(\text{radLon})$$

*Note: The parameter `altitudeOffset` is set to $0.002$ above the base planet radius to eliminate Z-fighting artifacts against terrain meshes.* 

### **3.3 Parametric Geometry Generation for Landing Ellipses**
To construct 3D landing ellipses centered at touchdown coordinates $(\psi_0, \phi_0)$ with semi-major angular radius $a$ and semi-minor angular radius $b$:

$$X(\theta) = r \cdot \cos(\psi_0 + a \cos\theta) \cdot \cos(\phi_0 + b \sin\theta)$$
$$Y(\theta) = r \cdot \sin(\psi_0 + a \cos\theta)$$
$$Z(\theta) = -r \cdot \cos(\psi_0 + a \cos\theta) \cdot \sin(\phi_0 + b \sin\theta)$$

Evaluating $\theta$ across $64$ discrete segments ($0 \le \theta \le 2\pi$) yields a smooth boundary curve and triangle fan geometry for rendering. 

---

## **4. Public Telemetry API Mirror Endpoints**
To preserve initial application load performance, traverse data is requested asynchronously upon hover interaction: 

| **Mission Platform** | **API Mirror Endpoint** | **Data Format** |
| :---: | :--- | :---: |
| **Opportunity** | [Opportunity JSON Mirror](https://azmth.space/data/mars-traverses/opportunity.json) | Parallel Array JSON |
| **Spirit** | [Spirit JSON Mirror](https://azmth.space/data/mars-traverses/spirit.json) | Parallel Array JSON |
| **Zhurong** | [Zhurong JSON Mirror](https://azmth.space/data/mars-traverses/zhurong.json) | Parallel Array JSON |
| **Sojourner** | [Sojourner JSON Mirror](https://azmth.space/data/mars-traverses/sojourner.json) | Parallel Array JSON |

---

## **5. Master Technical Data Patch for Completed & Failed Missions**
The following table provides verified geodetic coordinates, elevations, and operational classifications across all historical surface sites[cite: 2]: 

| **Mission ID** | **Station Memorial Name** | **Latitude (°N/S)** | **Longitude (°E)** | **Elevation (m MOLA)** | **Spatial Overlay Mode** |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `mer_opportunity` | Challenger Memorial Station[cite: 2] | $1.9462^\circ \text{S}$[cite: 2] | $354.4734^\circ \text{E}$[cite: 2] | $-1,390 \text{ m}$[cite: 2] | $45.16 \text{ km}$ Line String[cite: 2] |
| `mer_spirit` | Columbia Memorial Station[cite: 2] | $14.5684^\circ \text{S}$[cite: 2] | $175.4726^\circ \text{E}$[cite: 2] | $-1,910 \text{ m}$[cite: 2] | $7.73 \text{ km}$ Line String[cite: 2] |
| `zhurong_tianwen1` | Zhurong Landing Site[cite: 2] | $25.0660^\circ \text{N}$[cite: 2] | $109.9250^\circ \text{E}$[cite: 2] | $-4,099 \text{ m}$[cite: 2] | $1.92 \text{ km}$ Line String[cite: 2] |
| `pathfinder_sojourner` | Carl Sagan Memorial Station[cite: 2] | $19.0900^\circ \text{N}$[cite: 2] | $326.4800^\circ \text{E}$[cite: 2] | $-3,682 \text{ m}$[cite: 2] | $100 \text{ m}$ Local Line String[cite: 2] |
| `insight_lander` | Homestead Hollow Station[cite: 2] | $4.5020^\circ \text{N}$[cite: 2] | $135.6230^\circ \text{E}$[cite: 2] | $-2,613 \text{ m}$[cite: 2] | $130 \times 27 \text{ km}$ Ellipse / Workspace Ring[cite: 2] |
| `phoenix_lander` | Green Valley Station[cite: 2] | $68.2188^\circ \text{N}$[cite: 2] | $234.2508^\circ \text{E}$[cite: 2] | $-4,130 \text{ m}$[cite: 2] | $100 \times 20 \text{ km}$ Ellipse[cite: 2] |
| `viking_1` | Thomas Mutch Memorial Station[cite: 2] | $22.4800^\circ \text{N}$[cite: 2] | $312.0300^\circ \text{E}$[cite: 2] | $-3,627 \text{ m}$[cite: 2] | $280 \times 100 \text{ km}$ Historical Ellipse[cite: 2] |
| `viking_2` | Gerald Soffen Memorial Station[cite: 2] | $48.2690^\circ \text{N}$[cite: 2] | $134.0100^\circ \text{E}$[cite: 2] | $-3,820 \text{ m}$[cite: 2] | $280 \times 100 \text{ km}$ Historical Ellipse[cite: 2] |
| `beagle_2` | Isidis Planitia Station[cite: 2] | $11.5265^\circ \text{N}$[cite: 2] | $90.4295^\circ \text{E}$[cite: 2] | $-3,610 \text{ m}$[cite: 2] | Touchdown Point / Solar Panel Zone[cite: 2] |
| `mars_3_lander` | Ptolemaeus Station[cite: 2] | $45.0400^\circ \text{S}$[cite: 2] | $202.0200^\circ \text{E}$[cite: 2] | $+1,500 \text{ m}$[cite: 2] | Nominal Landing Zone Marker[cite: 2] |
| `schiaparelli_edm` | Meridiani Impact Site[cite: 2] | $2.0700^\circ \text{S}$[cite: 2] | $353.7900^\circ \text{E}$[cite: 2] | $-1,400 \text{ m}$[cite: 2] | Impact Zone Marker[cite: 2] |

---

## **6. Implementation Roadmap for WebGL Execution**
1. **Event Binding:** Attach `mouseenter` and `mouseleave` handlers to each `.landing-card` in the UI sidebar. 
2. **Lazy Material Caching:** Construct geometry objects on first hover and retain them in a `Map` data structure (`traverseCache`). 
3. **Visibility Toggling:** Toggle `mesh.visible = true / false` during hover state changes to preserve 60 FPS animation loop performance. 
4. **Visual Styling:** Use glowing cyan line materials (`#38bdf8`) for rover paths and translucent polygon fills (`opacity: 0.22`) for lander coverage zones.