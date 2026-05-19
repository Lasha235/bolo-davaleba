# 🎓 ფინალური პროექტი — Event Management Platform

> **Django REST Framework | Celery | Redis | Docker | PostgreSQL**

ეს არის კურსის ფინალური პროექტის დავალება. მიზანი არის სრულფასოვანი backend API-ს დაწერა, კურსზე განვლილი ყველა თემის გამოყენებით.

---

## 📋 პროექტის აღწერა

შექმენი **ღონისძიებების მართვის პლატფორმის API**, სადაც:

- **ორგანიზატორები** ქმნიან და მართავენ ღონისძიებებს
- **მომხმარებლები** პოულობენ და რეგისტრირდებიან ღონისძიებებზე
- **სისტემა** ავტომატურად აგზავნის ნოტიფიკაციებს, ამოწმებს ადგილებს და ინახავს სტატისტიკას

---

## 🗂️ მოდელები

შექმენი შემდეგი მოდელები. **ყოველი მოდელი ცალკე ფაილში არ უნდა იყოს** — გამოიყენე ლოგიკური დაჯგუფება `models.py`-ში.

### `CustomUser`
`AbstractUser`-ის გაფართოება.

| ველი | ტიპი | შენიშვნა |
|------|------|----------|
| `role` | `CharField` (choices) | `organizer` / `attendee` |
| `bio` | `TextField` | optional |
| `avatar` | `ImageField` | optional, upload_to='avatars/' |

### `Category`
| ველი | ტიპი |
|------|------|
| `name` | `CharField` |
| `slug` | `SlugField` (unique) |

### `Tag`
| ველი | ტიპი |
|------|------|
| `name` | `CharField` (unique) |

### `Event`
| ველი | ტიპი | შენიშვნა |
|------|------|----------|
| `title` | `CharField` | |
| `description` | `TextField` | |
| `organizer` | `ForeignKey(User)` | on_delete=CASCADE |
| `category` | `ForeignKey(Category)` | nullable |
| `tags` | `ManyToManyField(Tag)` | blank=True |
| `status` | `CharField` (choices) | `draft` / `published` / `cancelled` |
| `event_type` | `CharField` (choices) | `online` / `offline` |
| `start_date` | `DateTimeField` | |
| `end_date` | `DateTimeField` | |
| `location` | `CharField` | nullable (offline-სთვის) |
| `max_attendees` | `PositiveIntegerField` | |
| `created_at` | `DateTimeField` | auto_now_add |

### `Registration`
Many-to-Many **through** model — User და Event-ს შორის.

| ველი | ტიპი | შენიშვნა |
|------|------|----------|
| `user` | `ForeignKey(User)` | |
| `event` | `ForeignKey(Event)` | |
| `status` | `CharField` (choices) | `pending` / `confirmed` / `cancelled` |
| `registered_at` | `DateTimeField` | auto_now_add |

> ⚠️ `Meta`: `unique_together = ('user', 'event')` — ერთი მომხმარებელი ერთ ღონისძიებაზე მხოლოდ ერთხელ

### `Review`
| ველი | ტიპი | შენიშვნა |
|------|------|----------|
| `user` | `ForeignKey(User)` | |
| `event` | `ForeignKey(Event)` | |
| `rating` | `PositiveSmallIntegerField` | 1–5 |
| `comment` | `TextField` | |
| `created_at` | `DateTimeField` | auto_now_add |

> ⚠️ `Meta`: `unique_together = ('user', 'event')` — ერთი review per user per event

### `EventMedia`
| ველი | ტიპი | შენიშვნა |
|------|------|----------|
| `event` | `ForeignKey(Event)` | |
| `file` | `ImageField` | upload_to='event_media/' |
| `uploaded_at` | `DateTimeField` | auto_now_add |

---

## 🔌 API Endpoints

გამოიყენე `DefaultRouter` და `Nested Routers`.

### ავტორიზაცია
```
POST   /api/auth/register/
POST   /api/auth/login/          → JWT access + refresh token
POST   /api/auth/token/refresh/
POST   /api/auth/logout/
GET    /api/auth/me/             → current user profile
PATCH  /api/auth/me/             → profile განახლება
```

### Events
```
GET    /api/events/              → სია (ფილტრი, ძებნა, pagination)
POST   /api/events/              → შექმნა (მხოლოდ organizer)
GET    /api/events/{id}/
PATCH  /api/events/{id}/         → მხოლოდ საკუთარი event
DELETE /api/events/{id}/         → მხოლოდ საკუთარი event
GET    /api/events/stats/        → სტატისტიკა (cached)
POST   /api/events/{id}/media/   → სურათის ატვირთვა
```

### Registrations (Nested)
```
GET    /api/events/{id}/registrations/       → ივენთის მონაწილეები
POST   /api/events/{id}/registrations/       → რეგისტრაცია
PATCH  /api/events/{id}/registrations/{id}/  → სტატუსის შეცვლა (organizer)
DELETE /api/events/{id}/registrations/{id}/  → რეგისტრაციის გაუქმება
```

### Reviews (Nested)
```
GET    /api/events/{id}/reviews/
POST   /api/events/{id}/reviews/   → მხოლოდ confirmed attendee
PATCH  /api/events/{id}/reviews/{id}/
DELETE /api/events/{id}/reviews/{id}/
```

### Categories & Tags
```
GET    /api/categories/
GET    /api/tags/
```

---

## 🔐 Permissions

შექმენი **custom permission კლასები** `permissions.py`-ში:

| კლასი | აღწერა |
|-------|--------|
| `IsOrganizer` | `request.user.role == 'organizer'` |
| `IsOwnerOrReadOnly` | ობიექტის `organizer` ან read-only |
| `IsConfirmedAttendee` | review-სთვის: user-ს უნდა ჰქონდეს confirmed registration |

---

## 🔍 Filtering, Search, Pagination

`/api/events/` endpoint-ზე:

**ფილტრაცია** (`django-filter`):
- `status` — `?status=published`
- `event_type` — `?event_type=online`
- `category` — `?category=1`
- `start_date__gte` / `start_date__lte` — თარიღის range

**ძებნა** (`SearchFilter`):
- `?search=tbilisi` — ეძებს `title` და `description` ველებში

**სორტირება** (`OrderingFilter`):
- `?ordering=start_date` ან `?ordering=-created_at`

**Pagination**: `PageNumberPagination`, 10 ობიექტი გვერდზე

---

## 📊 Stats Endpoint

`GET /api/events/stats/` უნდა დააბრუნოს (ORM annotate/aggregate-ით):

```json
{
  "total_events": 42,
  "published_events": 35,
  "total_registrations": 312,
  "events_by_status": {
    "draft": 5,
    "published": 35,
    "cancelled": 2
  },
  "top_events": [
    {
      "id": 1,
      "title": "PyCon Georgia 2025",
      "registration_count": 98,
      "avg_rating": 4.7
    }
  ]
}
```

> 💡 გამოიყენე `annotate(Count(...), Avg(...))`, `values()`, `order_by()`

---

## ⏱️ Throttling

```python
'DEFAULT_THROTTLE_RATES': {
    'anon': '20/day',
    'user': '200/day',
    'registration_burst': '5/min',
}
```

Registration endpoint-ზე გამოიყენე `registration_burst` throttle class.

---

## 📧 Celery Tasks

### Task 1 — რეგისტრაციის ემეილი
`post_save` Signal Event Registration-ზე → async Celery task → HTML ემეილი.

ემეილი უნდა შეიცავდეს:
- ღონისძიების სახელი, თარიღი, ადგილი
- HTML template (`templates/emails/registration_confirmation.html`)
- ლოგოს inline attachment

### Task 2 — Periodic Reminder (Celery Beat)
ყოველ დილით 09:00-ზე: გაუგზავნე ემეილი ყველა მომხმარებელს, ვისაც ხვალ ღონისძიება აქვს.

```python
# celery.py-ში
app.conf.beat_schedule = {
    'send-event-reminders': {
        'task': 'events.tasks.send_event_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
}
```

---

## 🗄️ Caching (Redis)

| რა | როგორ | TTL |
|----|-------|-----|
| Event list | `cache.get/set` key-ით | 5 წუთი |
| Stats endpoint | `cache.get/set` | 5 წუთი |
| Cache invalidation | `post_save` / `post_delete` signal-ში | — |

```python
# მაგალითი
from django.core.cache import cache
import pickle

CACHE_KEY = 'events_list'

def get_events():
    cached = cache.get(CACHE_KEY)
    if cached:
        return pickle.loads(cached)
    events = Event.objects.filter(status='published').select_related('organizer', 'category')
    cache.set(CACHE_KEY, pickle.dumps(list(events)), timeout=300)
    return events
```

---

## 🐳 Docker

პროექტი უნდა გაეშვას **4 კონტეინერით**:

```
django    → gunicorn / runserver
postgres  → PostgreSQL 15
celery    → celery worker + beat
redis     → Redis 7
```

### `docker-compose.yml` სტრუქტურა

```yaml
services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: eventdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres

  redis:
    image: redis:7-alpine

  django:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - media_files:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file: .env

  celery:
    build: .
    command: celery -A config worker -l info -B
    depends_on:
      - redis
      - db
    env_file: .env

volumes:
  postgres_data:
  media_files:
```

### `.env` ფაილი (`.env.example` კომიტში)

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=eventdb
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## 🧪 ტესტები (Pytest)

მინიმუმ **15 ტესტი** `pytest` + `pytest-django`-ით.

### სავალდებულო კატეგორიები:

**Auth ტესტები:**
- [ ] რეგისტრაცია სწორი მონაცემებით
- [ ] რეგისტრაცია არასწორი მონაცემებით (validation error)
- [ ] Login და token მიღება

**Event ტესტები:**
- [ ] Event შექმნა organizer-ით ✅
- [ ] Event შექმნა attendee-ით ❌ (403)
- [ ] Event ჩამონათვალი (unauthorized user-ისთვისაც)
- [ ] ფილტრაცია სტატუსით

**Registration ტესტები:**
- [ ] წარმატებული რეგისტრაცია
- [ ] რეგისტრაცია სავსე ღონისძიებაზე (ადგილები ამოიწურა)
- [ ] ერთ ღონისძიებაზე ორჯერ რეგისტრაცია

**Review ტესტები:**
- [ ] Review confirmed attendee-ისგან ✅
- [ ] Review unregistered user-ისგან ❌ (403)

**Permission ტესტები:**
- [ ] სხვის event-ის რედაქტირება ❌ (403)
- [ ] საკუთარი event-ის წაშლა ✅

### Fixtures მაგალითი:

```python
# conftest.py
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def organizer(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='organizer1',
        password='pass1234',
        role='organizer'
    )

@pytest.fixture
def event(db, organizer):
    from events.models import Event
    return Event.objects.create(
        title='Test Event',
        organizer=organizer,
        status='published',
        max_attendees=10,
        start_date='2025-12-01 10:00:00+00:00',
        end_date='2025-12-01 18:00:00+00:00',
    )

@pytest.fixture
def api_client():
    return APIClient()
```

---

## 📁 პროექტის სტრუქტურა

```
event_platform/
│
├── config/                  ← Django project (settings, urls, celery)
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
│
├── apps/
│   ├── accounts/            ← CustomUser, auth views
│   ├── events/              ← Event, Category, Tag, Registration, Review, Media
│   └── notifications/       ← Celery tasks, email templates
│
├── templates/
│   └── emails/
│       └── registration_confirmation.html
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_events.py
│   ├── test_registrations.py
│   └── test_reviews.py
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── pytest.ini
└── README.md
```

---

## 📦 requirements.txt (მინიმუმი)

```
django>=4.2
djangorestframework
djangorestframework-simplejwt
django-filter
drf-nested-routers
drf-spectacular
celery
redis
django-redis
Pillow
psycopg2-binary
pytest-django
pytest
factory-boy
```

---

## 🐙 Git მოთხოვნები

**სავალდებულო:**
- ყოველი ფიჩერი **ცალკე branch**-ში იწერება
- Branch სახელები: `feature/auth`, `feature/events-api`, `feature/celery-tasks`, `feature/docker`, `feature/tests`
- Commit message-ები **მოკლე და ინფორმაციული**: `add JWT authentication`, `implement registration capacity check`
- `.env` ფაილი **არ** ინახება Git-ში (`.gitignore`-ში)
- `.env.example` **ინახება** Git-ში

---

## ✅ ჩაბარების Checklist

პროექტის ჩაბარებამდე შეამოწმე:

### მოდელები და ORM
- [ ] ყველა 6 მოდელი შექმნილია სწორი relationships-ით
- [ ] Migration ფაილები კომიტშია
- [ ] Custom Manager დაწერილია (მაგ. `PublishedEventManager`)

### API
- [ ] ყველა endpoint მუშაობს (Postman-ით შემოწმება)
- [ ] JWT ავტორიზაცია მუშაობს
- [ ] Custom permissions სწორად მუშაობს
- [ ] Filtering, Search, Pagination მუშაობს
- [ ] Throttling კონფიგურირებულია
- [ ] File upload მუშაობს

### Background Tasks
- [ ] Registration ემეილი იგზავნება async-ად
- [ ] Periodic reminder task კონფიგურირებულია
- [ ] HTML ემეილი template-ით

### Caching
- [ ] Event list-ი ქეშირდება
- [ ] Stats endpoint ქეშირდება
- [ ] Cache invalidation მუშაობს

### Docker
- [ ] `docker-compose up` ბრძანებით პროექტი ეშვება
- [ ] 4 კონტეინერი მუშაობს
- [ ] Migrations ავტომატურად გაეშვება

### ტესტები
- [ ] 15+ ტესტი დაწერილია
- [ ] `pytest` ბრძანება წარმატებით გაივლის

### დოკუმენტაცია
- [ ] Swagger UI ხელმისაწვდომია `/api/schema/swagger-ui/`-ზე
- [ ] README.md შეიცავს პროექტის დაყენების ინსტრუქციებს

---

## 🚀 პროექტის გაშვება (შეავსე)

```bash
# 1. კლონირება
git clone <your-repo-url>
cd event_platform

# 2. .env ფაილის შექმნა
cp .env.example .env
# შეავსე .env ფაილი

# 3. Docker-ით გაშვება
docker-compose up --build

# 4. Migrations
docker-compose exec django python manage.py migrate

# 5. Superuser შექმნა
docker-compose exec django python manage.py createsuperuser

# 6. ტესტების გაშვება
docker-compose exec django pytest
```

---

## 📬 ჩაბარება

- GitHub repository-ის ლინკი გამოაგზავნე
- Repository **public** უნდა იყოს
- ჩაბარების ვადა: **[თარიღი]**

---

> 💡 **რჩევა:** დაიწყე მოდელებით და migration-ებით, შემდეგ გააკეთე auth, შემდეგ events CRUD, და ბოლოს Celery + Docker.