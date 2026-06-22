# Passport Monitoring Dashboard

An AI-powered Passport Monitoring Dashboard that aggregates passport-related discussions, announcements, user experiences, and updates from multiple public data sources, processes them using Natural Language Processing (NLP) and Large Language Models (LLMs), and presents actionable insights through an interactive analytics dashboard.

---

## Live Demo

### Frontend

https://passport-monitoring-dashboard.vercel.app

### Backend API

https://passport-monitoring-dashboard.onrender.com

### API Documentation

https://passport-monitoring-dashboard.onrender.com/docs

---

# System Architecture

![System Architecture](docs/architecture.png)

---

# Overview

The Passport Monitoring Dashboard is designed to monitor, organize, analyze, and visualize passport-related information collected from multiple online sources.

The system automatically:

* Collects passport-related content
* Filters irrelevant or low-quality content
* Generates AI-powered summaries
* Detects sentiment
* Classifies content into categories
* Identifies duplicates
* Creates semantic clusters
* Enables translation
* Provides analytics and search capabilities

The goal is to help users quickly understand emerging passport-related trends and discussions without manually reviewing hundreds of individual posts.

---

# Key Features

## Data Ingestion

The platform continuously collects passport-related content from external public data sources.

Capabilities:

* Automated data collection
* Scheduled ingestion
* Duplicate prevention
* Metadata extraction
* Structured storage

---

## AI-Powered Analysis

Each post is processed using Large Language Models.

Generated insights include:

### AI Summary

Generates concise summaries for each post.

Example:

Original Content:
Long passport-related discussion

Generated Summary:
"User reports delay in passport renewal processing and seeks guidance."

---

### Sentiment Analysis

Determines emotional tone:

* Positive
* Neutral
* Negative

---

### Category Classification

Automatically categorizes posts into:

* Passport Application
* Passport Renewal
* Tatkal Services
* Appointments
* Travel Issues
* Government Announcements
* Visa Related
* Fraud / Scam Reports
* News
* Personal Experiences

---

### Language Detection

Automatically identifies the language of content.

---

### Gibberish Detection

Removes:

* Spam
* Bot-generated content
* Low-quality posts
* Meaningless text

---

# Semantic Search & Clustering

The platform uses semantic embeddings and clustering algorithms to group similar discussions.

Benefits:

* Duplicate reduction
* Topic discovery
* Trend identification
* Better dashboard readability

Workflow:

1. Generate embeddings
2. Calculate semantic similarity
3. Cluster related posts
4. Create grouped discussion threads

---

# Translation Engine

Supports multilingual accessibility.

Users can translate analyzed content into multiple languages directly from the dashboard.

Supported Languages:

* English
* Hindi
* Punjabi
* Spanish
* French
* German
* Arabic
* Chinese
* Russian
* Japanese

---

# Analytics Dashboard

Provides real-time insights:

### Content Analytics

* Total Posts
* Posts by Category
* Posts by Platform
* Posts by Language
* Posts by Sentiment

### Trend Analytics

* Emerging Topics
* Cluster Statistics
* Duplicate Detection Metrics

---

# Search & Filtering

Users can filter content by:

* Category
* Sentiment
* Language
* Source
* Date
* Engagement Metrics

Features:

* Full-text search
* Semantic search
* Advanced filtering

---

# Export Functionality

Supports exporting filtered results.

Available Formats:

* CSV
* Structured datasets for further analysis

---

# Technology Stack

## Frontend

* React
* TypeScript
* Vite
* Axios

## Backend

* FastAPI
* SQLAlchemy
* Pydantic

## Database

* PostgreSQL
* pgvector

## AI / NLP

* Groq LLM
* Sentence Transformers
* HDBSCAN
* Scikit-Learn

## Infrastructure

* Render
* Vercel

---

# System Workflow

1. Data Collection
2. Data Storage
3. AI Analysis
4. Embedding Generation
5. Semantic Clustering
6. Dashboard Visualization
7. Search & Filtering
8. Export

---

# API Endpoints

## Health Check

GET

/api/v1/health

---

## Posts

GET

/api/v1/posts

---

## Analytics

GET

/api/v1/analytics

---

## Clusters

GET

/api/v1/clusters

---

## Translation

POST

/api/v1/translate

---

## Analysis Pipeline

POST

/api/v1/pipeline/analyze

GET

/api/v1/pipeline/analyze/status

---

# Deployment Architecture

Frontend

Vercel

↓

Backend

Render

↓

PostgreSQL Database

↓

AI Processing Layer

---

# Future Enhancements

* Real-time streaming ingestion
* Enhanced trend forecasting
* PDF exports
* Geographical heatmaps
* User alerts and notifications
* Advanced topic modeling
* Dashboard personalization

---

# Author

Vansh

AI/ML Engineer | Generative AI Enthusiast

Portfolio: https://vanshbhutani.me

GitHub: https://github.com/vanshbhutani1405

LinkedIn: https://linkedin.com/in/vansh-62b84a184
