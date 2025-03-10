# **N-Port Holdings Lookup**
A Flask-based web application that allows users to look up **N-Port filings** from the SEC (Securities and Exchange Commission) and view fund holdings in a **Web3-inspired dark theme**. The application features **sorting, caching, and data visualization** using **Chart.js**.

---

## **🚀 Features**
✅ **Search N-Port Filings** using a **Fund CIK (Central Index Key)**  
✅ **Cachingr** to improve performance
✅ **Data Sorting** by **Value (USD), Balance, or Title**  
✅ **Data Visualization** via **Pie Chart** (Chart.js)  
✅ **CIK Cleanup** (Automatically removes `"CIK"` prefix)  
✅ **Search Persistence** (CIK remains in input field after search)  
✅ **Beautiful Dark UI** (TailwindCSS + Web3 Theme)  
✅ **Caching Enabled** (Flask-Caching to reduce API calls)  
✅ **Human-Readable Values** (`$` and commas added for easy reading)  
✅ **Deployed on Render** for public access  



---

## **🛠️ Technologies Used**
- **Flask** (Backend)
- **SEC API** (Data Source)
- **Chart.js** (Data Visualization)
- **Flask-Caching** (Performance Boost)
- **Tailwind CSS** (UI Styling)
- **Render** (Deployment)


## **📂 Project Structure**
```
/nport-holdings-lookup
│── app.py                   # Main Flask App
│── requirements.txt          # Dependencies
│── templates/
│   ├── index.html            # UI Template
│── README.md                 # Project Documentation
```

---

## **🌍 Deployment on Render**
The application is hosted on **Render**.  
Check it out here: **[LIVE DEMO LINK](https://nport-visualizer-prod.onrender.com/)**  

Example CIK: 0000884394

---

🚀 **Enjoy tracking your favorite fund holdings with N-Port Lookup!** 🎯
