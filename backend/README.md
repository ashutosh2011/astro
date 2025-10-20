# Astro MVP Backend

A FastAPI-based backend for Vedic astrology calculations and LLM-powered predictions.

## Features

- **Astronomical Calculations**: Swiss Ephemeris integration for accurate planetary positions
- **Vedic Astrology**: D1/D9 charts, Vimshottari dasha, yogas/doshas, SAV, transits
- **LLM Predictions**: OpenAI-powered astrological predictions with topic classification
- **Security**: JWT authentication, field-level encryption, rate limiting
- **Caching**: Redis-based caching for calculation results
- **Sensitivity Analysis**: Birth time uncertainty analysis

## Quick Start

### Prerequisites

- Python 3.11+
- Redis server
- OpenAI API key
- Swiss Ephemeris files

### Local Development

1. **Clone and setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Environment setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and secrets
   ```

3. **Download Swiss Ephemeris files**:
   ```bash
   mkdir ephemeris
   # Download ephemeris files from https://www.astro.com/swisseph/swephinfo_e.htm
   # Place sepl_18.se1, semo_18.se1, etc. in the ephemeris/ directory
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/healthz

### Docker Setup

1. **Using Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user info

### Profiles
- `POST /profiles` - Create profile
- `GET /profiles` - List profiles
- `GET /profiles/{id}` - Get profile
- `PATCH /profiles/{id}` - Update profile
- `DELETE /profiles/{id}` - Delete profile
- `GET /profiles/{id}/history` - Get profile history

### Calculations
- `POST /compute` - Run astrological calculations
- `GET /compute/{id}` - Get calculation snapshot

### Predictions
- `POST /predict/question` - Get astrological prediction
- `GET /predict/{id}` - Get prediction details

### Admin
- `GET /healthz` - Health check
- `GET /readyz` - Readiness check
- `DELETE /admin/cache/reset/{profile_id}` - Reset cache (admin only)
- `GET /admin/stats` - Get statistics (admin only)

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./astro.db

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Encryption
ENCRYPTION_KEY=your-32-byte-base64-encryption-key-change-this

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Swiss Ephemeris
EPHEMERIS_PATH=./ephemeris

# App settings
APP_NAME=Astro MVP Backend
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO
```

### Swiss Ephemeris Files

Download the required ephemeris files from [Astro.com](https://www.astro.com/swisseph/swephinfo_e.htm):

- `sepl_18.se1` - Planetary positions
- `semo_18.se1` - Moon positions
- `seas_18.se1` - Asteroids
- `sefstars_18.se1` - Fixed stars

Place these files in the `ephemeris/` directory.

## Database Migrations

### Using Alembic

1. **Create migration**:
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   ```

2. **Apply migration**:
   ```bash
   alembic upgrade head
   ```

3. **Downgrade**:
   ```bash
   alembic downgrade -1
   ```

## Rate Limits

- `/compute`: 10 requests/minute
- `/predict/question`: 5 requests/minute
- Other endpoints: 60 requests/minute
- Burst: 2x for 10 seconds

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Field Encryption**: Sensitive data encrypted at rest
- **Rate Limiting**: Prevents abuse and DoS attacks
- **Input Validation**: Comprehensive validation of all inputs
- **Error Handling**: Secure error messages without information leakage

## Calculation Features

### Supported Calculations

1. **D1 Chart (Rashi)**: Planetary positions, houses, ascendant
2. **D9 Chart (Navamsha)**: Signs only for D9 analysis
3. **Panchanga**: Tithi, nakshatra, pada, yoga, karana
4. **Dignities**: Exaltation, debilitation, own signs, combustion
5. **Aspects**: Parashari aspects with orb calculations
6. **Vimshottari Dasha**: MD/AD calculations with next 12 months
7. **Transits**: Current positions of Saturn, Jupiter, Rahu, Ketu
8. **SAV (Ashtakavarga)**: Sarvashtakavarga calculations
9. **Yogas/Doshas**: 11 curated yogas and doshas
10. **Bhava Bala**: House strength calculations
11. **Sensitivity Analysis**: Birth time uncertainty analysis

### Supported Ayanamsas

- Lahiri (default)
- Raman
- KP (Krishnamurti)
- Fagan-Bradley
- Yukteshwar

### Supported House Systems

- Whole Sign (default)
- Placidus
- Koch
- Equal

## LLM Integration

### Topic Classification

Questions are automatically classified into:
- Career
- Marriage
- Health
- Travel
- General

### Prediction Format

```json
{
  "topic": "career",
  "answer": {
    "summary": "Your career prospects look promising...",
    "time_windows": [
      {
        "start": "2024-03-01",
        "end": "2024-06-30",
        "focus": "promotion/role-shift",
        "confidence": 0.8
      }
    ],
    "actions": [
      "Focus on networking in March-April",
      "Prepare for interviews in May-June"
    ],
    "risks": [
      "Avoid major decisions during Mercury retrograde"
    ],
    "evidence": [
      {
        "calc_field": "timing.current_md",
        "value": "Moon",
        "interpretation": "Current MD activates career house"
      }
    ],
    "confidence_topic": 0.75
  },
  "confidence_overall": 0.72
}
```

## Development

### Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app
│   ├── config.py                  # Configuration
│   ├── api/                       # API endpoints
│   ├── services/                  # Business logic
│   │   ├── calc_engine/           # Astrological calculations
│   │   └── llm/                   # LLM integration
│   ├── models/                    # Database models
│   ├── schemas/                   # Pydantic schemas
│   └── utils/                     # Utilities
├── alembic/                       # Database migrations
├── docker-compose.yml             # Docker setup
├── Dockerfile                     # Docker image
└── requirements.txt               # Dependencies
```

### Adding New Features

1. **New Calculations**: Add to `services/calc_engine/`
2. **New Endpoints**: Add to `api/`
3. **New Models**: Add to `models/`
4. **New Schemas**: Add to `schemas/`

### Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app
```

## Production Deployment

### Docker Production

1. **Build production image**:
   ```bash
   docker build -t astro-backend .
   ```

2. **Run with production settings**:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e DEBUG=False \
     -e DATABASE_URL=postgresql://user:pass@host:port/db \
     astro-backend
   ```

### Environment Variables for Production

- Set `DEBUG=False`
- Use strong `JWT_SECRET_KEY`
- Use strong `ENCRYPTION_KEY`
- Use PostgreSQL instead of SQLite
- Set up Redis cluster for high availability
- Configure proper logging levels

## Troubleshooting

### Common Issues

1. **Swiss Ephemeris errors**: Ensure ephemeris files are in correct location
2. **Redis connection errors**: Check Redis server is running
3. **OpenAI API errors**: Verify API key and rate limits
4. **Database errors**: Check database connection and migrations

### Logs

```bash
# View application logs
docker-compose logs -f api

# View Redis logs
docker-compose logs -f redis
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API docs at `/docs`

