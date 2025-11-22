# RAG Customer Support System

An intelligent customer support automation system using Retrieval-Augmented Generation (RAG) with Google Gemini and Pinecone.

## 🎯 Features

- **📄 PDF Knowledge Ingestion**: Upload documents via Telegram bot
- **🤖 AI-Powered Responses**: Automated email replies using RAG
- **🔍 Semantic Search**: Pinecone vector database for accurate retrieval
- **📧 Gmail Integration**: Automatic email monitoring and responses
- **🔐 Secure**: OAuth 2.0 authentication for Gmail

## 📁 Project Structure

```
RAG Demo/
├── app/
│   ├── config/          # Configuration management
│   ├── services/        # Business logic services
│   │   ├── agent_service.py
│   │   ├── gmail_service.py
│   │   ├── ingestion_service.py
│   │   └── vector_store_service.py
│   └── utils/           # Utility functions
│       └── logger.py
├── logs/                # Application logs
├── tests/               # Unit tests
├── .env                 # Environment variables
├── credentials.json     # Gmail OAuth credentials
├── requirements.txt     # Python dependencies
└── run.py              # Main entry point
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your credentials:
- `GOOGLE_API_KEY`: Google Gemini API key
- `PINECONE_API_KEY`: Pinecone API key
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `PINECONE_INDEX_NAME`: Your Pinecone index name

- Note : You may have to create .env file.

### 3. Setup Gmail
Place your `credentials.json` file (from Google Cloud Console) in the project root.

### 4. Run the Application

**Start Telegram Ingestion Bot:**
```bash
python3 run.py ingest
```

**Start Email Support Agent:**
```bash
python3 run.py agent
```

**Custom polling interval:**
```bash
python3 run.py agent --poll-interval 30
```

## 📚 Documentation

- **QUICKSTART.md**: Detailed setup instructions
- **gmail_setup_guide.md**: Gmail OAuth setup guide

## 🛠️ Tech Stack

- **LLM**: Google Gemini (gemini-pro)
- **Embeddings**: Google Gemini Embeddings (models/embedding-001)
- **Vector DB**: Pinecone
- **Framework**: LangChain
- **Telegram**: python-telegram-bot
- **Email**: Gmail API

## 📝 License

MIT License
