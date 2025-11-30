# Flux ⚡ - AI Email Automation

An intelligent customer support automation system using Retrieval-Augmented Generation (RAG) with multi-LLM support and real-time email processing.

## 🎯 Features

- **📧 Gmail Integration**: Secure OAuth 2.0 authentication with automatic email monitoring
- **🤖 AI-Powered Responses**: Automated email replies using RAG with multi-LLM fallback (Gemini, Claude)
- **📄 Knowledge Base**: Web-based PDF upload and management with semantic search
- **📊 Real-Time Dashboard**: Beautiful analytics with ApexCharts and live data updates
- **🔐 Separated Auth**: Clean architecture with distinct landing and dashboard experiences
- **🌐 Multi-User Support**: Isolated data per user with session-based authentication
- **⚡ Sub-Second Processing**: Lightning-fast email classification and response generation

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with required credentials:
```env
# LLM Configuration
GOOGLE_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_claude_api_key  # Optional fallback
LLM_PRIMARY_PROVIDER=gemini
LLM_FALLBACK_PROVIDERS=claude

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_index_name
VECTOR_DB_TYPE=pinecone
```

### 3. Setup Gmail OAuth
Follow the **[OAuth Setup Guide](docs/guides/OAUTH_SETUP.md)** to configure Gmail API credentials.

### 4. Run the Application
```bash
# Start the web dashboard
python wsgi.py

# In another terminal, start the email agent
python run.py agent --poll-interval 60
```

Access the dashboard at `http://127.0.0.1:5001`

## 🛠️ Tech Stack

### Backend
- **Python 3.12+**
- **Flask** - Web framework with Blueprint architecture
- **Multi-LLM Support**: Gemini (primary), Claude (fallback)
- **Embeddings**: Google Gemini Embeddings (embedding-004)
- **Vector DB**: Pinecone (with abstraction for future providers)
- **Email**: Gmail API with OAuth 2.0

### Frontend
- **Vanilla JavaScript** - No framework dependencies
- **ApexCharts** - Beautiful, interactive charts
- **Flatpickr** - Date range selection
- **Modern CSS** - Glassmorphism, gradients, animations

### Architecture
- **Application Factory Pattern** - Scalable Flask setup
- **Provider System** - Abstract LLM and Vector DB providers with automatic fallback
- **Separated Auth/Dashboard** - Clean routing with `/` (landing) and `/dashboard`
- **Multi-User Isolation** - Session-based auth with per-user data segregation

## 📚 Documentation

### 🎯 Start Here
- **[Main Documentation Index](docs/README.md)** - Complete documentation map
- **[Product Requirements (PRD)](docs/PRD.md)** - Full product specifications

### 📖 For Users
- **[Main Walkthrough](docs/walkthroughs/main_walkthrough.md)** - Installation and usage guide
- **[OAuth Setup Guide](docs/guides/OAUTH_SETUP.md)** - Gmail API configuration
- **[Gmail Setup Guide](docs/guides/gmail_setup_guide.md)** - Detailed Gmail integration

### 🏗️ For Developers
- **[Architecture Overview](docs/architecture/README.md)** - System design and components
- **[High-Level Design](docs/architecture/HIGH_LEVEL_DESIGN.md)** - Deployment and scalability
- **[Sequence Diagrams](docs/architecture/SEQUENCE_DIAGRAMS.md)** - Detailed workflow diagrams
- **[Code Walkthrough](docs/walkthroughs/code_walkthrough.md)** - Critical code flows
- **[Multi-LLM Architecture](docs/architecture/llm/README.md)** - LLM provider system
- **[Multi-Vector DB Architecture](docs/architecture/vector_db/README.md)** - Vector DB abstraction

### 🎨 For AI Engineers
- **[Prompts Guide](docs/prompts/README.md)** - System prompts and templates

## 🌟 Key Capabilities

### Email Processing
- **Automatic Classification**: Intelligent email categorization using LLM
- **RAG-Enhanced Responses**: Context-aware replies using knowledge base
- **Multi-User Isolation**: Each user's data completely segregated
- **Domain Filtering**: Configurable domain exclusion list

### Dashboard
- **Real-Time Analytics**: Email volume charts, category distribution
- **Custom Date Ranges**: Flexible time period selection with Flatpickr
- **Activity Logs**: Detailed processing history with filtering
- **Knowledge Base Viewer**: Browse uploaded documents with pagination

### Web Architecture
- **Landing Page** (`/`): Unauthenticated landing with features showcase
- **Dashboard** (`/dashboard`): Protected dashboard with metrics and charts
- **Client-Side Routing**: Smart redirects based on auth status in `auth.js`
- **Auto-Refresh**: Dashboard updates every 30 seconds

## 🔧 Development

### Project Structure
```
RAG-Demo/
├── app/
│   ├── api/              # REST API routes
│   ├── web/              # Web page routes
│   ├── services/         # Business logic
│   │   ├── llm_providers/     # Multi-LLM system
│   │   ├── vector_db_providers/ # Vector DB abstraction
│   │   └── gmail/             # Gmail sub-services
│   ├── static/
│   │   ├── css/          # Stylesheets
│   │   ├── js/           # Client-side logic
│   │   └── images/       # Static assets
│   └── templates/        # Jinja2 templates
├── docs/                 # Comprehensive documentation
├── run.py               # CLI entry point
└── wsgi.py              # Web server entry point
```

### Running Tests
```bash
pytest tests/
```

## 📊 Architecture Highlights

### Multi-LLM Fallback
```
Gemini (primary) → Claude (fallback) → Exponential backoff retry
```
- Automatic provider switching on quota errors (HTTP 429)
- Configurable fallback chain via environment variables
- Transparent to application code

### Separated Auth Flow
```
/ (landing.html) ←→ /dashboard (dashboard.html)
         ↑                    ↑
         └─── auth.js ────────┘
              (redirects based on session)
```

### Data Fetching Architecture
```
dashboard.js → /api/metrics/summary → Database
charts.js    → /api/metrics/email-volume → Database
             → /api/metrics/categories → Database
```

## 🎥 Demo Videos

https://github.com/user-attachments/assets/97c3da8f-53a3-40ea-b103-be73e20b46c4


https://github.com/user-attachments/assets/be54516a-fe79-4b1a-bfe4-4f97a222ad29



## 🤝 Contributing

This is an educational project showcasing RAG implementation with production-ready patterns. Feel free to fork and extend!

## 📝 License

MIT License

---

**Last Updated**: November 30, 2025  
**Architecture**: Multi-LLM ✅ | Multi-Vector DB ✅ | Separated Auth/Dashboard ✅
