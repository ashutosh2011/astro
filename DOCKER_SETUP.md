# Astro MVP - Docker Compose Setup

This Docker Compose configuration runs the complete Astro MVP Backend stack with all required services.

## Services Included

- **PostgreSQL Database** (port 5432) - Main application database
- **Redis Cache** (port 6379) - Caching and rate limiting
- **FastAPI Backend** (port 8000) - Main application server with enhanced chat capabilities
- **Database Migration** - Runs Alembic migrations on startup

## Quick Start

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f backend
   ```

3. **Stop services:**
   ```bash
   docker-compose down
   ```

4. **Stop and remove volumes (WARNING: This will delete all data):**
   ```bash
   docker-compose down -v
   ```

## Enhanced Chat Features

The chat system has been significantly improved with:

- **Better LLM Model**: Upgraded from gpt-4o-mini to gpt-4o for superior reasoning
- **Comprehensive Context**: Full astrological data including birth charts, dashas, transits, yogas
- **Enhanced Responses**: Longer, more detailed responses (up to 2000 tokens)
- **Better Reasoning**: Structured analytical framework with detailed explanations
- **Temporal Analysis**: Past, present, and future astrological influences
- **Conversation Memory**: Extended chat history (20 messages) for better context

## Configuration

The Docker Compose file includes enhanced defaults for better chat performance. For production, you should:

1. **Change security keys** in the environment variables:
   - `SECRET_KEY`
   - `JWT_SECRET_KEY` 
   - `ENCRYPTION_KEY`

2. **Set your OpenAI API key** (required for chat features):
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   docker-compose up -d
   ```

3. **Update CORS origins** for your frontend URLs

4. **LLM Settings** (already optimized):
   - `LLM_MODEL`: gpt-4o (best reasoning capability)
   - `LLM_MAX_TOKENS`: 2000 (comprehensive responses)
   - `LLM_TEMPERATURE`: 0.7 (balanced creativity)
   - `LLM_TIMEOUT_MS`: 30000 (sufficient processing time)

## Testing Chat Improvements

To test the enhanced chat functionality:

1. **Run the test script:**
   ```bash
   ./test_docker_chat.sh
   ```

2. **Test chat endpoint manually:**
   ```bash
   # First, create a profile and get authentication token
   # Then test the chat endpoint
   curl -X POST http://localhost:8000/chat/message \
     -H 'Content-Type: application/json' \
     -H 'Authorization: Bearer YOUR_TOKEN' \
     -d '{"profile_id": 1, "message": "Tell me about my career prospects"}'
   ```

3. **Expected improvements:**
   - Responses should be 600-1000 words (vs previous 250 words)
   - More detailed astrological analysis
   - Better reasoning and explanations
   - Comprehensive context from all astrological data
   - Structured response format with multiple sections

## API Endpoints

Once running, the API will be available at:
- **Base URL:** http://localhost:8000
- **Health Check:** http://localhost:8000/healthz
- **API Documentation:** http://localhost:8000/docs
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **Chat Endpoint:** http://localhost:8000/chat/message

## Database Access

To connect to the PostgreSQL database directly:
- **Host:** localhost
- **Port:** 5432
- **Database:** astro_db
- **Username:** astro_user
- **Password:** astro_password

## Redis Access

To connect to Redis directly:
- **Host:** localhost
- **Port:** 6379
- **No password required**

## Troubleshooting

### Backend won't start
- Check if PostgreSQL and Redis are healthy: `docker-compose ps`
- View backend logs: `docker-compose logs backend`

### Database connection issues
- Ensure PostgreSQL is running: `docker-compose logs postgres`
- Check if migrations completed: `docker-compose logs migrate`

### Redis connection issues
- Check Redis logs: `docker-compose logs redis`
- The backend will work without Redis (caching disabled)

## Development

For development with live reload:
```bash
# Run backend in development mode
docker-compose up postgres redis -d
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Production Notes

- Use proper secrets management
- Set up SSL/TLS termination
- Configure proper logging
- Set up monitoring and alerting
- Use external managed databases for production
