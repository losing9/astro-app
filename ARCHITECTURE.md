# Astrogunluk.tr Architecture

## 1. Database Schema (PostgreSQL)

### `users`
- `id` (UUID, PK)
- `email` (String, Unique)
- `password_hash` (String)
- `first_name` (String)
- `last_name` (String)
- `birth_date` (Date)
- `birth_time` (Time)
- `birth_city` (String)
- `latitude` (Float)
- `longitude` (Float)
- `credits` (Integer, Default 0)
- `tier` (Enum: 'free', 'premium')
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

### `natal_charts`
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `chart_data` (JSONB) - Contains planets, houses, aspects.
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

### `daily_transits`
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `date` (Date)
- `transit_data` (JSONB) - Contains transit positions and active aspects with natal chart.
- `generated_text` (Text) - LLM generated personalized horoscope.
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

### `generated_reports`
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `report_type` (Enum: '3_month_transit', 'synastry', etc.)
- `parameters` (JSONB)
- `pdf_url` (String, nullable)
- `status` (Enum: 'pending', 'processing', 'completed', 'failed')
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

### `payments`
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `amount` (Decimal)
- `currency` (String)
- `provider` (Enum: 'iyzico', 'paytr')
- `transaction_id` (String)
- `status` (Enum: 'success', 'failed', 'pending')
- `created_at` (Timestamp)

### `subscriptions`
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `plan_name` (String)
- `status` (Enum: 'active', 'canceled', 'expired')
- `start_date` (Timestamp)
- `end_date` (Timestamp)

---

## 2. Swiss Ephemeris Data Pipeline Architecture

**Astrological Logic & Data Engine (AntiGravity)**

The pipeline is designed as a Python module utilizing `pyswisseph` (Swiss Ephemeris).

**Step 1: Natal Chart Calculation**
- Input: User's UTC birth datetime, latitude, longitude.
- Action: Call `swe_calc_ut` for Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Node. Call `swe_houses` for Placidus house cusps.
- Output: Standardized JSON dictionary with degrees, signs, and retrograde status.

**Step 2: Transit Calculation**
- Input: Date (00:00 UTC).
- Action: Calculate planetary positions for the given day.
- Output: JSON dictionary with transit degrees.

**Step 3: Aspect Calculation**
- Input: Natal positions, Transit positions, predefined Orbs.
- Action: Compute angular distances. Filter out aspects outside of orbs.
- Output: JSON list of active aspects (e.g., Transit Jupiter Trine Natal Sun).

---

## 3. Background Job & Queue Logic

**Queue Worker System (Celery + Redis)**
- **Daily Cron Job**: A Celery beat schedule runs daily at 02:00 AM. It fetches all active users.
- **Task Distribution**: For each user, a task `generate_daily_horoscope_task(user_id, date)` is pushed to the Redis queue.
- **Worker Execution**:
  1. Retrieve user's natal chart and calculate today's transits.
  2. Compute aspects.
  3. Format data into the Prompt Template.
  4. Call OpenAI API (async) to generate text.
  5. Cache result in Redis (`user:{id}:horoscope:{date}`) and store in `daily_transits` table.
- **Notifications**: Push tasks to `send_notification_task` at 08:30 AM.

---

## 4. Prompt Template

```python
SYSTEM_PROMPT = """You are an expert, empathetic astrologer.
You are provided with a user's natal chart and today's planetary transits and aspects in JSON format.
Analyze this data and write a highly personalized, insightful daily horoscope.
Keep it under 150 words. Focus on the most exact transit aspects.
Tone: Encouraging, insightful, professional."""

def get_daily_horoscope_prompt(user_name, natal_json, transit_json, aspects_json):
    return f"""
User: {user_name}
Natal Chart Data: {natal_json}
Current Transits: {transit_json}
Active Transit Aspects to Natal: {aspects_json}

Based on the above astrological data, please generate the personalized daily horoscope.
"""
```

---

## 5. API Endpoints Specification

### Authentication
- `POST /api/v1/auth/register` - Create user and trigger natal chart calculation.
- `POST /api/v1/auth/login` - Return JWT token.

### Horoscopes & Reports
- `GET /api/v1/horoscope/daily` - Get today's horoscope (cached <100ms).
- `POST /api/v1/reports/request` - Request a premium PDF report (deduct credits, enqueue task).
- `GET /api/v1/reports` - List user's reports.

### AI Astro-Bot
- `POST /api/v1/bot/chat` - Ask a question to the AI (deducts tokens, contextualized with natal chart).

### Payments
- `POST /api/v1/payments/checkout` - Initialize payment (Iyzico/PayTR).
- `POST /api/v1/payments/webhook` - Webhook for payment gateway to confirm successful transaction.
