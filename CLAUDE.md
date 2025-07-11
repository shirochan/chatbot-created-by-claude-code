# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Run the Streamlit chatbot app
uv run streamlit run src/app.py

# Run on specific port
uv run streamlit run src/app.py --server.port=8502
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run tests with detailed failure info
uv run pytest -vvs

# Run specific test file
uv run pytest tests/test_app.py -v
```

### Docker Development
```bash
# Build production image
docker build -t chatbot-app .

# Build development image (includes tests)
docker build --target builder -t chatbot-app-dev .

# Run tests in container
docker run --rm chatbot-app-dev uv run pytest -v
```

### Package Management
```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Add development dependency
uv add --group dev package-name
```

## Architecture Overview

This is a multi-provider AI chatbot built with Streamlit and LangChain that supports OpenAI, Anthropic, and Google models with multimodal capabilities (image and PDF file upload).

### Core Components

**Models Layer (`src/models/`)**
- `factory.py`: Central model factory that creates LangChain model instances based on provider
- `config.py`: Model definitions with provider mappings, API key requirements, descriptions, and vision support flags
- Supports 5 models across 3 providers:
  - GPT-4o (OpenAI): OpenAIの最新マルチモーダルモデル - 🖼️ Vision support
  - GPT-4.1 (OpenAI): 最新のGPTモデル、コーディングと推論が大幅向上 - 📝 Text only
  - Claude Sonnet 4 (Anthropic): スマートで効率的な日常使いに最適なモデル - 🖼️ Vision support
  - Claude Opus 4 (Anthropic): 世界最高のコーディングモデル、最も知的なAI - 🖼️ Vision support
  - Gemini 2.5 Flash (Google): 思考機能付きハイブリッド推論モデル、速度と効率重視 - 🖼️ Vision support

**File Processing Layer (`src/utils/file_processing.py`)**
- Image processing with PIL/Pillow: supports PNG, JPG, JPEG, GIF, BMP, WebP formats
  - File size limit: 10MB per image
  - Maximum resolution: 2048x2048 pixels
  - Quality setting: 95% for processed images
- PDF text extraction with dual-engine approach: pdfplumber (primary) + PyPDF2 (fallback)
  - File size limit: 50MB per PDF
  - Preview length: 500 characters
- Base64 encoding for image transmission to LLM APIs
- Comprehensive error handling and logging

**Chat History Management Layer (`src/utils/database.py` & `src/utils/history_manager.py`)**
- SQLite database for persistent chat history storage
- Automatic conversation saving and retrieval
- Individual conversation deletion capabilities
- Automatic backup system with 24-hour intervals
- Maximum conversation limits: 1000 conversations, 500 messages per conversation

**Configuration System**
- `config.yaml`: Central app configuration (UI settings, logging, chat behavior, file upload settings)
  - File upload settings: supported formats, size limits (10MB images, 50MB PDFs), processing quality
  - Chat history settings: auto-save, backup intervals, conversation limits
  - Streamlit UI configuration: layout, sidebar state, page settings
- Environment variables: API keys for each provider (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`)
- Model availability determined by presence of corresponding API keys
- Database configuration: SQLite path, backup settings, retention policies

**App Flow (`src/app.py`)**
1. Load configuration and environment variables
2. Initialize available models based on API keys
3. Setup chat history database and management system
4. Streamlit UI with model selection sidebar, file upload widget, and chat history panel
5. Process uploaded files (images/PDFs) with size/format validation and display previews
6. Chat interface converts messages to LangChain format (including multimodal content)
7. Send images as base64-encoded content to vision-capable models
8. Save conversations automatically to database with backup scheduling
9. Error handling with provider-specific error messages and comprehensive logging

### Key Design Patterns

**Provider Abstraction**: All AI providers accessed through unified LangChain interface via factory pattern

**Dynamic Model Selection**: Available models determined at runtime based on configured API keys

**Configuration-Driven**: UI, logging, and behavior controlled via `config.yaml` rather than hardcoded values

**Error Categorization**: HTTP status codes mapped to user-friendly error messages (401→API key invalid, 429→rate limit, etc.)

**Multimodal Support**: Automatic detection of vision-capable models with appropriate content encoding (base64 for images, text extraction for PDFs)

**Dual-Engine Processing**: Fallback mechanisms for robust file processing (pdfplumber → PyPDF2 for PDFs)

**Database-Driven History**: Persistent chat history with SQLite backend, automatic backup, and conversation management

**Configuration-First Approach**: All limits, settings, and behaviors configurable via YAML without code changes

### Environment Setup Requirements

Create `.env` file with API keys for desired providers:
```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here  
GOOGLE_API_KEY=your_key_here
```

Only models with valid API keys will appear in the UI.