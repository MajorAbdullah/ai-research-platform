# AI Research Platform - Local Hosting Setup

This is the clean local hosting version of the AI Research Platform, optimized for deployment on local hosting services.

## 🚀 Quick Start

### Prerequisites
- Python 3.13+ 
- pip package manager

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MajorAbdullah/ai-research-platform.git
   cd ai-research-platform
   git checkout local-hosting
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python run_local.py
   ```

The application will start on `http://localhost:8000`

## 🌐 Web Interface

- **Main Interface:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs (FastAPI auto-generated)
- **Health Check:** http://localhost:8000/health

## 📋 Features

- **AI-Powered Research:** Multiple research types (Custom, Validation, Market, Financial, Comprehensive)
- **Multiple AI Models:** Support for O3 Deep Research and O4 Mini models
- **Real-time Progress:** Live updates during research processing
- **Export Options:** Download reports in Markdown format
- **Local Database:** SQLite database for storing research results
- **Clean Interface:** Modern web interface with progress tracking

## 🏗️ Architecture

- **Backend:** FastAPI (Python)
- **Database:** SQLite (local file-based)
- **Frontend:** Pure HTML/JavaScript with Tailwind CSS
- **AI Integration:** OpenAI API compatible research client

## 📁 Project Structure

```
research agent/
├── app.py                 # Main FastAPI application
├── run_local.py          # Local launcher script
├── requirements.txt      # Python dependencies
├── research_platform.db  # SQLite database (auto-created)
├── api/                  # API routes
├── models/              # Database models
├── services/            # Business logic services
├── research_documents/  # Generated research reports
└── config/             # Configuration files
```

## 🔧 Configuration

The application uses local configuration with no cloud dependencies:

- **Database:** Local SQLite file (`research_platform.db`)
- **Storage:** Local file system for research documents
- **Models:** OpenAI API (requires API key in environment)

### Environment Variables

Create a `.env` file (optional):

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## 🐳 Docker Support (Optional)

If you prefer Docker deployment:

```bash
# Build image
docker build -t research-platform .

# Run container
docker run -p 8000:8000 research-platform
```

## 📊 API Endpoints

### Research Operations
- `POST /api/research` - Start new research
- `GET /api/research/{task_id}/status` - Check research status
- `GET /api/research/results` - Get all results

### Models & Info
- `GET /api/models` - Available AI models
- `GET /health` - Health check

## 🚦 Health Monitoring

The application includes built-in health monitoring:

- **Database connectivity**
- **Research client status** 
- **Active tasks count**
- **System resource usage**

## 🔒 Security Notes

This local hosting version:
- ✅ Removed all cloud-specific configurations
- ✅ Uses local SQLite database
- ✅ No external service dependencies (except OpenAI API)
- ✅ Clean, minimal codebase for hosting providers

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Python version issues:**
   - Ensure Python 3.13+ is installed
   - Use virtual environment

3. **Database issues:**
   - Delete `research_platform.db` to reset
   - Application will recreate automatically

4. **Missing dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## 📞 Support

For hosting providers or deployment questions, contact the development team.

---

**Note:** This is the local hosting branch optimized for deployment. The main branch contains the full cloud-integrated version.
