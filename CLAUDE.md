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
- Supports 5 models across 3 providers: GPT-4o/4.1 (OpenAI), Claude Sonnet 4/Opus 4 (Anthropic), Gemini 2.5 Flash (Google)
- Vision support: GPT-4o, Claude Sonnet 4, Claude Opus 4, and Gemini 2.5 Flash support image understanding

**File Processing Layer (`src/utils/file_processing.py`)**
- Image processing with PIL/Pillow: supports PNG, JPG, JPEG, GIF, BMP, WebP formats
- PDF text extraction with dual-engine approach: pdfplumber (primary) + PyPDF2 (fallback)
- Base64 encoding for image transmission to LLM APIs
- Comprehensive error handling and logging

**Configuration System**
- `config.yaml`: Central app configuration (UI settings, logging, chat behavior, file upload settings)
- Environment variables: API keys for each provider (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`)
- Model availability determined by presence of corresponding API keys
- File upload configuration: supported formats, size limits, processing settings

**App Flow (`src/app.py`)**
1. Load configuration and environment variables
2. Initialize available models based on API keys
3. Streamlit UI with model selection sidebar and file upload widget
4. Process uploaded files (images/PDFs) and display previews
5. Chat interface converts messages to LangChain format (including multimodal content)
6. Send images as base64-encoded content to vision-capable models
7. Error handling with provider-specific error messages

### Key Design Patterns

**Provider Abstraction**: All AI providers accessed through unified LangChain interface via factory pattern

**Dynamic Model Selection**: Available models determined at runtime based on configured API keys

**Configuration-Driven**: UI, logging, and behavior controlled via `config.yaml` rather than hardcoded values

**Error Categorization**: HTTP status codes mapped to user-friendly error messages (401→API key invalid, 429→rate limit, etc.)

**Multimodal Support**: Automatic detection of vision-capable models with appropriate content encoding (base64 for images, text extraction for PDFs)

**Dual-Engine Processing**: Fallback mechanisms for robust file processing (pdfplumber → PyPDF2 for PDFs)

### Environment Setup Requirements

Create `.env` file with API keys for desired providers:
```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here  
GOOGLE_API_KEY=your_key_here
```

Only models with valid API keys will appear in the UI.