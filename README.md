# Odoo HR Bot

An AI-powered HR assistant that provides intelligent responses to employee questions about company policies, onboarding procedures, and HR-related inquiries using Retrieval-Augmented Generation (RAG) technology.

## Features

- **Intelligent Query Routing**: Automatically routes questions to appropriate handlers (onboarding vs HR policy)
- **RAG-Based Responses**: Uses document retrieval and reranking for accurate, context-aware answers
- **Role-Based Access Control**: Different permissions based on user roles (admin, employee, etc.)
- **Real-time Communication**: WebSocket support for instant messaging
- **Document Processing**: Supports PDF and DOCX handbook ingestion
- **Conversation Memory**: Maintains chat history for contextual responses
- **JWT Authentication**: Secure user authentication with refresh token support

## Tech Stack

- **Backend**: FastAPI with Python 3.8+
- **LLM**: OpenAI GPT-4o-mini
- **Vector Database**: Milvus (via Zilliz Cloud)
- **Embeddings**: OpenAI text-embedding-3-small
- **Reranking**: Cross-encoder models for relevance scoring
- **Authentication**: JWT with bcrypt password hashing

## Project Structure

```
├── api/                    # API routes
│   ├── auth_routes.py     # Authentication endpoints
│   └── chain_routes.py    # Main RAG query endpoint
├── authentication/        # Auth logic
│   └── auth.py            # JWT and user management
├── config/                # Configuration files
│   ├── app.yaml           # Application settings
│   └── prompts.yaml       # LLM prompts and templates
├── schemas/               # Pydantic models
│   ├── query.py           # Query schema
│   ├── state_schema.py    # Chat state schema
│   ├── token.py           # Token schemas
│   └── user.py            # User schemas
├── scripts/               # Utility scripts
│   ├── chat.py            # CLI chat interface
│   ├── debug_retriever.py # Debug document retrieval
│   ├── ingest.py          # Document ingestion
│   ├── meh.py             # Utility for dropping collections
│   └── server.py          # Simple development server
├── src/                   # Core application logic
│   ├── embeddings.py      # Embedding model setup
│   ├── ingest.py          # Document processing
│   ├── llm.py             # OpenAI client wrapper
│   ├── loaders.py         # Document loaders
│   ├── main.py            # Core RAG pipeline
│   ├── prompts.py         # Prompt rendering
│   ├── rag.py             # RAG chain logic
│   ├── reranker.py        # Document reranking
│   ├── router.py          # Query routing logic
│   └── vectorstore.py     # Milvus integration
├── utils/                 # Utilities
│   ├── __init__.py
│   ├── config_loader.py   # Configuration management
│   ├── constants.py       # Application constants
│   └── utils.py           # Helper functions
├── ws/                    # WebSocket handling
│   ├── helper.py          # WebSocket auth helpers
│   └── ws_routes.py       # WebSocket endpoints
├── .env.example           # Environment variable template
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
└── test.html              # Sample chat interface HTML
```

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Zilliz Cloud account (managed Milvus)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd odoo-hr-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment configuration**
   ```bash
   cp .env.example .env
   ```
   
   Fill in your `.env` file:
   ```env
   # LLM
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Zilliz Cloud (Milvus-as-a-service)
   ZILLIZ_REGION=gcp-us-west1
   ZILLIZ_ID=your_cluster_id_here
   ZILLIZ_TOKEN=your_zilliz_token_here
   
   # HuggingFace (private or rate-limited models)
   HUGGINGFACEHUB_API_TOKEN=hf_xxx
   
   # FastAPI
   SECRET_KEY=your_secret_key_here
   ```

4. **Prepare your handbook documents**
   - Create a `data/handbook/` directory
   - Add your PDF or DOCX files containing HR policies and procedures

5. **Ingest documents into vector database**
   ```bash
   python -m scripts.ingest
   ```

## Usage

### Starting the Server

```bash
uvicorn main:app --reload
```

The server will start on `http://localhost:8000` with the following endpoints:

- **API Documentation**: `http://localhost:8000/docs`
- **Authentication**: `/auth/*`
- **Query Endpoint**: `/api/ask`
- **WebSocket**: `/ws/{token}`

### Authentication Flow

1. **Sign up** (POST `/auth/signup`)
   ```json
   {
     "username": "john_doe",
     "email": "john@company.com", 
     "password": "secure_password",
     "role": "employee"
   }
   ```

2. **Login** (POST `/auth/login`)
   ```json
   {
     "username": "john_doe",
     "password": "secure_password"
   }
   ```

3. **Use the returned access token** in subsequent requests

### Asking Questions

**REST API**:
```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the sick leave policy?"}'
```

**WebSocket**: Connect to `/ws/{token}` and send:
```json
{"query": "What equipment do new hires receive?"}
```

### CLI Interface

For development and testing:
```bash
python -m scripts.chat --q "What is the vacation policy?" --role employee
```

## Configuration

### Application Settings (`config/app.yaml`)

Configure LLM, embeddings, vector database, and other components:

```yaml
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.3

embedding:
  provider: openai
  model: text-embedding-3-small
  dim: 1536

reranker:
  type: cross_encoder
  model: cross-encoder/ms-marco-MiniLM-L-6-v2
  candidates: 8
  top_n: 4
```

### Prompts (`config/prompts.yaml`)

Customize the system prompts for different scenarios:
- Welcome message
- Router prompt for query classification
- HR policy response template
- Onboarding assistance template

## User Roles

- **employee**: Standard access to HR information
- **admin/hr-admin/it-admin**: Full access including administrative information

## Development

### Testing Document Retrieval

Debug what documents are being retrieved:
```bash
python -m scripts.debug_retriever
```

### Running Development Server

Simple development server without full FastAPI features:
```bash
python -m scripts.server
```

### Adding New Document Types

Extend `src/loaders.py` to support additional file formats by adding new loader functions.

## API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/users/me/` - Get current user info
- `POST /auth/refresh` - Refresh access token

### Query Processing
- `POST /api/ask` - Submit questions to the HR bot

### WebSocket
- `WS /ws/{token}` - Real-time chat interface

## Frontend Integration

The included `test.html` file demonstrates a complete chat interface. For production use:

1. **Token Management**: Replace the hardcoded `bearerToken` variable with the actual user's access token after authentication:
   ```javascript
   const bearerToken = 'USER_ACCESS_TOKEN_AFTER_LOGIN';
   ```

2. **Authentication Flow**: Implement proper login flow that:
   - Calls `/auth/login` to get access token
   - Stores the token securely
   - Uses the token for WebSocket connection
   - Handles token refresh when needed

## Deployment

The application is designed for cloud deployment with:
- Zilliz Cloud for vector storage
- OpenAI for LLM inference
- FastAPI for production-ready API serving

### Production Considerations

1. **Environment Variables**: Ensure all required environment variables are set
2. **Document Updates**: Re-run ingestion when handbook documents change
3. **Model Caching**: Models are loaded once at startup for efficiency
4. **Logging**: Comprehensive logging for monitoring and debugging
5. **Security**: JWT tokens with configurable expiration times

## Contributing

1. Follow the existing code structure and patterns
2. Add appropriate logging for new features
3. Update configuration files when adding new components
4. Test document ingestion after making changes to loaders
5. Ensure proper error handling and user feedback
