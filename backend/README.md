Backend (Django + DRF)

Quick start
- python3 -m venv .venv && source .venv/bin/activate
- pip install -r requirements.txt (or pip install Django==4.2.* djangorestframework django-cors-headers)
- python manage.py migrate
- python manage.py runserver 0.0.0.0:8000

API base
- http://localhost:8000/api/
- All endpoints accept an anonymous ID via header X-Client-Id, or query/body param client_id. The backend will read and store per client ID.

Auth
- POST /api/auth/login { email, password }
  - Returns { ok, user:{id,email,name}, token }
  - Accepts any non-empty email and password; demo email test@demo.com supported.
- POST /api/auth/anon {}
  - Returns { ok, user:{id,email:'anon@local',name}, token }
  - If client_id not provided, a new anon:xxxx is generated and returned.

Moods
- GET /api/moods?days=7
  - Returns { ok, data:[{ date:'YYYY-MM-DD', score, note?, at }] }
- POST /api/moods { score:1-5, note? }
  - One record per day; if already recorded, returns 409 with message "今天已记录".
- GET /api/moods/summary
  - Returns { ok, data:{ average:Number, count:Number } }

Assessment
- POST /api/assessment/submit { answers:[9 numbers 0-3] }
  - Returns { ok, data:{ total, level, crisis, ai:{summary,recommendations[],risk_level}, at } }
  - Level bands: 0–4 none-minimal, 5–9 mild, 10–14 moderate, 15–19 moderately severe, 20–27 severe. Crisis if Q9>0.
- GET /api/assessment/last
  - Returns { ok, data|null }

Chat
- POST /api/chat { message }
  - If sensitive words detected (e.g. 自杀/不想活/suicide), returns crisis payload with hotlines.
  - Else returns a supportive fallback message. Place to integrate AI later.

Survey
- POST /api/survey/sus { answers:[10 numbers 1-5] } -> { ok }
- POST /api/survey/satisfaction { score:1-5, comment? } -> { ok }

CORS
- Allowed origins: http://localhost:5173 and http://localhost:5174
- Credentials enabled; custom header X-Client-Id allowed and exposed.

Admin
- Create superuser: python manage.py createsuperuser
- Admin panel: /admin/

Database
- Default: SQLite at backend/db.sqlite3
- To switch DB, edit server/settings.py DATABASES.

Logging
- Console logging enabled for django and api loggers.



