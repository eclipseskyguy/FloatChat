# 🌊 FloatChat: Conversational AI for ARGO Ocean Data  

## 📖 Background  

Oceanographic data is vast, complex, and heterogeneous – ranging from satellite observations to in-situ measurements like CTD casts, Argo floats, and BGC sensors.  

The **Argo program**, which deploys autonomous profiling floats across the world’s oceans, generates an extensive dataset in **NetCDF format** containing temperature, salinity, and other essential ocean variables.  

Accessing, querying, and visualizing this data usually requires domain expertise, technical skills, and familiarity with complex formats and tools.  

With the rise of **AI and Large Language Models (LLMs)**, especially when combined with modern structured databases and interactive dashboards, it is now feasible to create **intuitive, accessible systems that democratize access to ocean data**.  

---

## 🎯 Problem Statement  

The goal of **FloatChat** is to develop an **AI-powered conversational system** for ARGO float data that enables users to **query, explore, and visualize oceanographic information** using natural language.  

---

## ✅ Core Features  

- 📥 **Data Ingestion**  
  - Ingest ARGO NetCDF files and convert them into structured formats (SQL + Parquet).  

- 🔎 **Metadata Retrieval**  
  - Store float metadata and summaries in a **vector database** (FAISS/Chroma) for efficient search and retrieval.  

- 🤖 **AI-Powered Querying**  
  - Use Retrieval-Augmented Generation (**RAG**) pipelines powered by multimodal LLMs (GPT, Qwen, LLaMA, Mistral).  
  - Translate user questions into database queries (SQL) via **Model Context Protocol (MCP)**.  

- 📊 **Interactive Dashboards**  
  - Visualize float data with geospatial maps, depth-time plots, trajectory overlays, and profile comparisons using **Streamlit + Plotly/Leaflet/Cesium**.  

- 💬 **Chat Interface**  
  - Natural language interaction for non-technical users.  
  - Example queries:  
    - *"Show me salinity profiles near the equator in March 2023"*  
    - *"Compare BGC parameters in the Arabian Sea for the last 6 months"*  
    - *"What are the nearest ARGO floats to this location?"*  

---

## 📐 Expected Solution Architecture  

- **Data Layer**:  
  - NetCDF ingestion → Parquet + SQL (SQLite/PostgreSQL).  
  - Metadata stored in FAISS/Chroma for semantic retrieval.  

- **Backend (AI + Query Engine)**:  
  - RAG pipeline maps natural language queries → SQL queries.  
  - Returns structured + summarized outputs.  

- **Frontend (User Experience)**:  
  - Jupyter Notebooks for demo & exploration.  
  - Streamlit dashboard for interactive visualization.  
  - Chatbot interface for guided data discovery.  

- **Demo Scope**:  
  - Proof-of-Concept (PoC) with **Indian Ocean ARGO data**.  
  - Extensible to BGC floats, gliders, buoys, and satellite datasets.  

---

## 📂 Project Structure  

