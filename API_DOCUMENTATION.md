# Astro MVP Backend API Documentation

## Overview

This document provides comprehensive API documentation for the Astro MVP Backend, a Vedic astrology calculation and prediction service built with FastAPI.

**Base URL**: `http://localhost:8000` (development)  
**API Version**: v1.0.0  
**Authentication**: Bearer Token (JWT)

## Table of Contents

1. [Authentication](#authentication)
2. [Profiles](#profiles)
3. [Calculations](#calculations)
4. [Predictions](#predictions)
5. [Admin](#admin)
6. [Health Checks](#health-checks)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)

---

## Authentication

### Register User
**POST** `/auth/register`

Creates a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses:**
- `400` - Invalid email or password format
- `500` - Registration failed

---

### Login User
**POST** `/auth/login`

Authenticates user and returns access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses:**
- `401` - Invalid email or password
- `500` - Login failed

---

### Logout User
**POST** `/auth/logout`

Logs out user (client should discard token).

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

### Get Current User
**GET** `/auth/me`

Returns current authenticated user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Profiles

### Create Profile
**POST** `/profiles/`

Creates a new astrological profile for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "John Doe",
  "gender": "male",
  "dob": "1990-05-15",
  "tob": "14:30",
  "tz": "America/New_York",
  "place": "New York, NY",
  "lat": 40.7128,
  "lon": -74.0060,
  "altitude_m": 10,
  "uncertainty_minutes": 5,
  "ayanamsa": "Lahiri",
  "house_system": "WholeSign"
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "John Doe",
  "gender": "male",
  "dob": "1990-05-15",
  "tob": "14:30",
  "tz": "America/New_York",
  "place": "New York, NY",
  "lat": 40.7128,
  "lon": -74.0060,
  "altitude_m": 10,
  "uncertainty_minutes": 5,
  "ayanamsa": "Lahiri",
  "house_system": "WholeSign",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### List Profiles
**GET** `/profiles/`

Retrieves paginated list of user's profiles.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1, min: 1)
- `per_page` (optional): Items per page (default: 20, min: 1, max: 100)

**Response (200):**
```json
{
  "profiles": [
    {
      "id": 1,
      "name": "John Doe",
      "gender": "male",
      "dob": "1990-05-15",
      "tob": "14:30",
      "tz": "America/New_York",
      "place": "New York, NY",
      "lat": 40.7128,
      "lon": -74.0060,
      "altitude_m": 10,
      "uncertainty_minutes": 5,
      "ayanamsa": "Lahiri",
      "house_system": "WholeSign",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

---

### Get Profile
**GET** `/profiles/{profile_id}`

Retrieves a specific profile by ID.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "name": "John Doe",
  "gender": "male",
  "dob": "1990-05-15",
  "tob": "14:30",
  "tz": "America/New_York",
  "place": "New York, NY",
  "lat": 40.7128,
  "lon": -74.0060,
  "altitude_m": 10,
  "uncertainty_minutes": 5,
  "ayanamsa": "Lahiri",
  "house_system": "WholeSign",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- `404` - Profile not found

---

### Update Profile
**PATCH** `/profiles/{profile_id}`

Updates an existing profile. Only provided fields will be updated.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "John Smith",
  "uncertainty_minutes": 10
}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "John Smith",
  "gender": "male",
  "dob": "1990-05-15",
  "tob": "14:30",
  "tz": "America/New_York",
  "place": "New York, NY",
  "lat": 40.7128,
  "lon": -74.0060,
  "altitude_m": 10,
  "uncertainty_minutes": 10,
  "ayanamsa": "Lahiri",
  "house_system": "WholeSign",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

---

### Get Profile History
**GET** `/profiles/{profile_id}/history`

Retrieves calculation snapshots and predictions history for a profile.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "profile_id": 1,
  "history": [
    {
      "type": "calc_snapshot",
      "id": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "metadata": {
        "ruleset_version": "1.0.0",
        "ephemeris_version": "sepl_18",
        "ayanamsa": "Lahiri",
        "house_system": "WholeSign"
      }
    },
    {
      "type": "prediction",
      "id": 1,
      "created_at": "2024-01-01T01:00:00Z",
      "metadata": {
        "question": "Will I get a new job soon?",
        "topic": "career",
        "confidence_overall": 0.75,
        "llm_model": "gpt-4o-mini"
      }
    }
  ],
  "total": 2
}
```

---

### Delete Profile
**DELETE** `/profiles/{profile_id}`

Deletes a profile and all associated calculations and predictions.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Profile deleted successfully"
}
```

---

## Calculations

### Compute Astrological Calculations
**POST** `/compute/`

Performs comprehensive astrological calculations for a profile or inline birth data.

**Headers:** `Authorization: Bearer <token>`

**Request Body (using profile):**
```json
{
  "profile_id": 1
}
```

**Request Body (inline birth data):**
```json
{
  "name": "John Doe",
  "gender": "male",
  "dob": "1990-05-15",
  "tob": "14:30",
  "tz": "America/New_York",
  "place": "New York, NY",
  "lat": 40.7128,
  "lon": -74.0060,
  "altitude_m": 10,
  "uncertainty_minutes": 5,
  "ayanamsa": "Lahiri",
  "house_system": "WholeSign"
}
```

**Response (200):**
```json
{
  "calc_snapshot_id": 1,
  "input_hash": "a1b2c3d4e5f6...",
  "ruleset_version": "1.0.0",
  "ephemeris_version": "sepl_18",
  "ayanamsa": "Lahiri",
  "house_system": "WholeSign",
  "calc_timestamp": "2024-01-01T00:00:00Z",
  "cached": false
}
```

**Error Responses:**
- `400` - Invalid birth data or profile not found
- `503` - Calculation service unavailable

---

### Get Calculation Snapshot
**GET** `/compute/{calc_snapshot_id}`

Retrieves detailed calculation results by snapshot ID.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "input_hash": "a1b2c3d4e5f6...",
  "ayanamsa": "Lahiri",
  "house_system": "WholeSign",
  "ephemeris_version": "sepl_18",
  "ruleset_version": "1.0.0",
  "created_at": "2024-01-01T00:00:00Z",
  "data": {
    "meta": {
      "ayanamsa": "Lahiri",
      "house_system": "WholeSign",
      "timezone": "America/New_York",
      "dst_used": true,
      "ephemeris": "SwissEph",
      "calc_timestamp": "2024-01-01T00:00:00Z",
      "ruleset_version": "1.0.0"
    },
    "panchanga": {
      "weekday": "Tuesday",
      "tithi": "Shukla Paksha 5",
      "nakshatra": "Rohini",
      "pada": 2,
      "yoga": "Siddhi",
      "karana": "Bava"
    },
    "d1": {
      "ascendant": {
        "sign": "Leo",
        "degree": 15.5,
        "nakshatra": "Magha",
        "pada": 1
      },
      "planets": [
        {
          "name": "Sun",
          "sign": "Taurus",
          "degree": 25.3,
          "house": 9,
          "nakshatra": "Rohini",
          "pada": 3
        }
      ],
      "houses": [
        {
          "house": 1,
          "sign": "Leo",
          "degree": 15.5,
          "lord": "Sun"
        }
      ]
    },
    "dignities": {
      "exaltation": ["Sun"],
      "debilitation": [],
      "mooltrikona": ["Sun", "Moon"],
      "own_sign": ["Mars", "Venus"]
    },
    "aspects": {
      "planetary_aspects": [
        {
          "planet": "Mars",
          "aspects": [
            {
              "target": "Jupiter",
              "type": "7th",
              "strength": 0.8
            }
          ]
        }
      ]
    },
    "dasha": {
      "current_md": "Moon",
      "current_ad": "Mars",
      "next_12m_ads": [
        {
          "dasha": "Mars",
          "start_date": "2024-02-01",
          "end_date": "2024-03-15"
        }
      ]
    },
    "transits": {
      "saturn_house_from_lagna": 7,
      "jupiter_house_from_lagna": 10,
      "rahu_ketu_axis_from_lagna": [2, 8],
      "sade_sati_phase": "none"
    },
    "d9": {
      "asc_sign": "Sagittarius",
      "planet_signs": {
        "Sun": "Gemini",
        "Moon": "Cancer"
      },
      "d9_better": {
        "Sun": true,
        "Moon": false
      }
    },
    "sav": [28, 31, 34, 29, 32, 30, 33, 31, 29, 34, 32, 30],
    "yogas": [
      {
        "name": "Gajakesari Yoga",
        "planets": ["Jupiter", "Moon"],
        "strength": 0.7
      }
    ],
    "bhava_bala": [0.72, 0.54, 0.68, 0.61, 0.75, 0.58, 0.69, 0.63, 0.71, 0.66, 0.73, 0.59],
    "sensitivity": {
      "lagna_flips": false,
      "moon_sign_flips": false,
      "d9_asc_flips": false,
      "dasha_boundary_risky": false
    }
  }
}
```

---

## Predictions

### Ask Prediction Question
**POST** `/predict/question`

Gets AI-powered astrological prediction for a specific question.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "profile_id": 1,
  "question": "Will I get a new job soon?",
  "time_horizon_months": 12
}
```

**Response (200):**
```json
{
  "prediction_id": 1,
  "topic": "career",
  "answer": {
    "summary": "Your career prospects look promising in the next 6 months. The current planetary transits favor professional growth and new opportunities. Jupiter's transit through your 10th house indicates potential for advancement, while Mars in your career sector suggests increased energy and drive for professional pursuits.",
    "time_windows": [
      {
        "start": "2024-03-01",
        "end": "2024-06-30",
        "focus": "promotion/role-shift",
        "confidence": 0.8
      },
      {
        "start": "2024-07-01",
        "end": "2024-09-30",
        "focus": "new opportunities",
        "confidence": 0.7
      }
    ],
    "actions": [
      "Focus on networking in March-April when Jupiter aspects your career house",
      "Prepare for interviews in May-June during favorable Mars transit",
      "Consider upskilling opportunities during Mercury's beneficial period",
      "Update your resume and LinkedIn profile in February"
    ],
    "risks": [
      "Avoid major career decisions during Mercury retrograde periods",
      "Be cautious of overly aggressive negotiations in late April"
    ],
    "evidence": [
      {
        "calc_field": "transits.jupiter_house_from_lagna",
        "value": 10,
        "interpretation": "Jupiter in 10th house indicates career growth opportunities"
      },
      {
        "calc_field": "dasha.current_md",
        "value": "Moon",
        "interpretation": "Current MD activates emotional intelligence for career success"
      },
      {
        "calc_field": "d1.planets.Sun.house",
        "value": 9,
        "interpretation": "Sun in 9th house suggests recognition and higher learning"
      }
    ],
    "confidence_topic": 0.75
  },
  "confidence_overall": 0.72,
  "sensitivity_notice": null,
  "calc_snapshot_id": 1,
  "llm_model": "gpt-4o-mini",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- `400` - Profile not found or no calculation snapshot available
- `500` - LLM service error

---

### Get Prediction
**GET** `/predict/{prediction_id}`

Retrieves a specific prediction by ID.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "question": "Will I get a new job soon?",
  "topic": "career",
  "result": {
    "topic": "career",
    "answer": {
      "summary": "Your career prospects look promising...",
      "time_windows": [],
      "actions": [],
      "risks": [],
      "evidence": [],
      "confidence_topic": 0.75
    },
    "confidence_overall": 0.72
  },
  "confidence_overall": 0.72,
  "llm_model": "gpt-4o-mini",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Admin

### Admin Health Check
**GET** `/admin/healthz`

Basic health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### Admin Readiness Check
**GET** `/admin/readyz`

Comprehensive readiness check including database and Redis connectivity.

**Response (200):**
```json
{
  "status": "ready",
  "database": "healthy",
  "redis": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Response (503):**
```json
{
  "status": "not_ready",
  "database": "unhealthy",
  "redis": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### Reset Profile Cache
**DELETE** `/admin/cache/reset/{profile_id}`

Clears cache for a specific profile (admin only).

**Headers:** `Authorization: Bearer <admin_token>`

**Response (200):**
```json
{
  "message": "Cache cleared for profile 1",
  "cleared_keys": 5,
  "admin_user": "admin@example.com"
}
```

---

### Reset All Cache
**DELETE** `/admin/cache/reset/all`

Clears all cache (admin only).

**Headers:** `Authorization: Bearer <admin_token>`

**Response (200):**
```json
{
  "message": "Clear all cache not implemented yet",
  "admin_user": "admin@example.com",
  "note": "Use profile-specific cache reset instead"
}
```

---

### Get Admin Statistics
**GET** `/admin/stats`

Returns system statistics (admin only).

**Headers:** `Authorization: Bearer <admin_token>`

**Response (200):**
```json
{
  "total_users": 150,
  "total_profiles": 300,
  "total_calc_snapshots": 500,
  "total_predictions": 750,
  "redis_status": "healthy",
  "admin_user": "admin@example.com"
}
```

---

## Health Checks

### Liveness Probe
**GET** `/healthz`

Basic application health check.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": 1704067200.0
}
```

---

### Readiness Probe
**GET** `/readyz`

Application readiness check.

**Response (200):**
```json
{
  "status": "ready",
  "timestamp": 1704067200.0
}
```

---

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human readable error message",
  "details": "Additional error details (optional)",
  "request_id": "uuid-string"
}
```

### Common Error Codes

- `VALIDATION_ERROR` - Invalid input data
- `AUTHENTICATION_ERROR` - Invalid credentials
- `AUTHORIZATION_ERROR` - Insufficient permissions
- `NOT_FOUND_ERROR` - Resource not found
- `CALCULATION_ERROR` - Astrological calculation failed
- `LLM_ERROR` - AI prediction service error
- `RATE_LIMIT_ERROR` - Too many requests
- `INTERNAL_SERVER_ERROR` - Unexpected server error

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **General endpoints**: 100 requests per minute
- **Compute endpoints**: 20 requests per minute
- **Prediction endpoints**: 10 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit` - Request limit per window
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Reset` - Time when the rate limit resets

When rate limit is exceeded, a `429` status code is returned with:
```json
{
  "error": "RATE_LIMIT_ERROR",
  "message": "Rate limit exceeded",
  "request_id": "uuid-string"
}
```

---

## Authentication

### JWT Token Usage

Include the JWT token in the Authorization header for all protected endpoints:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Expiration

- Access tokens expire after 30 minutes (1800 seconds)
- Refresh tokens are not implemented in this version
- Clients should handle token expiration gracefully

---

## Data Validation

### Profile Data Validation

- **Name**: 1-50 characters
- **Gender**: Must be "male" or "female"
- **Date of Birth**: Valid date in YYYY-MM-DD format
- **Time of Birth**: HH:MM or HH:MM:SS format (24-hour)
- **Timezone**: Valid IANA timezone identifier
- **Place**: 1-100 characters
- **Latitude**: -90 to 90 degrees
- **Longitude**: -180 to 180 degrees
- **Altitude**: -500 to 10,000 meters
- **Uncertainty**: 0-10 minutes
- **Ayanamsa**: Valid ayanamsa system (default: "Lahiri")
- **House System**: Valid house system (default: "WholeSign")

### Question Validation

- **Question**: 1-500 characters
- **Time Horizon**: 1-24 months

---

## CORS

The API supports CORS for cross-origin requests. Configured origins are defined in the application settings.

---

## Request/Response Headers

### Standard Headers

- `Content-Type: application/json`
- `Authorization: Bearer <token>` (for protected endpoints)
- `X-Request-ID: <uuid>` (automatically added)
- `X-Process-Time: <seconds>` (response processing time)

---

## Examples

### Complete Workflow Example

1. **Register User**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123"}'
```

2. **Create Profile**
```bash
curl -X POST "http://localhost:8000/profiles/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "John Doe",
    "gender": "male",
    "dob": "1990-05-15",
    "tob": "14:30",
    "tz": "America/New_York",
    "place": "New York, NY",
    "lat": 40.7128,
    "lon": -74.0060
  }'
```

3. **Run Calculation**
```bash
curl -X POST "http://localhost:8000/compute/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"profile_id": 1}'
```

4. **Ask Prediction**
```bash
curl -X POST "http://localhost:8000/predict/question" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "profile_id": 1,
    "question": "Will I get a new job soon?",
    "time_horizon_months": 12
  }'
```

---

## Support

For technical support or questions about the API, please contact the development team.

**API Version**: 1.0.0  
**Last Updated**: January 2024
