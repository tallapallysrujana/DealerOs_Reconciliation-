# Dealer Os Reconciliation System

A full-stack application for comparing data between two systems (System A and System B) to identify disagreements in event records across multiple tenants.

## Tech Stack

- **Backend:** Django 4.2.23, Django REST Framework, Django Filter
- **Frontend:** React 19 with Vite
- **Styling:** Custom CSS with Inter font

## Project Structure

```
Dealer Os/
├── backend/                 # Django backend
│   ├── comparison/          # Main Django app
│   │   ├── models.py       # Database models
│   │   ├── views.py        # REST API views
│   │   ├── serializers.py  # API serializers
│   │   ├── admin.py        # Django admin configuration
│   │   ├── tests.py        # Unit tests
│   │   └── management/     # Django management commands
│   │       └── commands/
│   │           ├── import_csv.py
│   │           └── compare_systems.py
│   ├── config/             # Django project configuration
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── requirements.txt    # Python dependencies
│   ├── locations.csv       # Sample location data
│   ├── system_a.csv        # Sample System A data
│   └── system_b.csv        # Sample System B data
├── frontend/              # React frontend
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   ├── api.js          # API client
│   │   ├── App.css         # Component styling
│   │   └── main.jsx        # React entry point
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
├── README.md              # This file
├── DECISIONS.md           # Architectural decisions
└── .gitignore             # Git ignore rules
```

## How to Run

### Prerequisites

- Python 3.8+
- Node.js 16+
- pip
- npm

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run database migrations:**
```bash
python manage.py migrate
```

4. **Import CSV data:**
```bash
python manage.py import_csv --locations locations.csv --system-a system_a.csv --system-b system_b.csv
```

5. **Run comparison logic:**
```bash
python manage.py compare_systems
```

6. **Start Django server:**
```bash
python manage.py runserver
```

Backend will run on `http://127.0.0.1:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install Node dependencies:**
```bash
npm install
```

3. **Start React development server:**
```bash
npm run dev
```

Frontend will run on `http://localhost:5173`

### Access the Application

- **Frontend UI:** http://localhost:5173
- **Backend API:** http://127.0.0.1:8000/api/disagreements/
- **Admin Panel:** http://127.0.0.1:8000/admin/ (admin/admin123)

## What I Built

### ✅ Completed Features

1. **Data Import with Dirty Data Handling**
   - CSV import management command
   - Normalizes dirty record_ref formats (rec1034, REC1070, 1112 → REC-1034)
   - Handles malformed decimal values (1,25,400.00)
   - Survives missing locations and blank fields
   - No rows silently dropped

2. **Comparison Logic**
   - Detects 4 types of disagreements:
     - Records missing in System B (2 found)
     - Orphan entries pointing to non-existent records (1 found)
     - Duplicate entries for same record (2 found)
     - Value mismatches between systems (5 found)
   - Total: 10 disagreements identified in test dataset

3. **REST API**
   - Filter by disagreement type
   - Filter by organization (tenant isolation)
   - Sort by values, dates, and record IDs
   - CORS enabled for frontend communication

4. **React Frontend**
   - Table display of all disagreements
   - Filter by disagreement type and organization
   - Sort by value and other fields
   - Clean dark theme with Inter font
   - Responsive design

5. **Testing**
   - Unit tests for all 4 disagreement types
   - Test for correct matching (no false positives)
   - All 5 tests pass successfully

6. **Admin Interface**
   - View and manage all data
   - Inspect imported records
   - Review disagreements

## What I Deliberately Did Not Build

1. **Authentication** - Skipped as per brief guidelines
2. **User Management** - Not required for single-user demo
3. **Real-time Updates** - Not needed for static comparison
4. **Export Functionality** - Could be added but not essential
5. **Advanced Analytics** - Basic comparison meets requirements
6. **Data Validation UI** - Admin panel sufficient for inspection
7. **Performance Optimization** - Dataset too small to warrant optimization
8. **Error Recovery UI** - Basic error handling sufficient
9. **Mobile App** - Responsive web design adequate
10. **Automated Testing Pipeline** - Manual tests sufficient for evaluation

## How I Worked with the Agent

I used Claude (via the Claude.ai coding tools) as a pair programmer for this whole build. My workflow was: I fed it the actual brief and the real CSVs first, and had it inspect the data directly (row counts, regex scans for malformed `record_ref` values, a script to diff System A totals against System B values) before writing any code, rather than guessing at what "dirty data" might look like. That surfaced the specific quirks this README references — `rec1034`, the split entry on `REC-1055`, System B recording `base_value` instead of `total_value` on a few rows — which then became the actual test fixtures, not synthetic ones.

From there we worked in the order: models → importers → matching logic → tests → API → UI → docs, committing after each stage, and I ran the test suite and the importer against the real files after every stage rather than at the end, so a mistake in an early layer wouldn't compound silently into the next one.

---

## Required Questions

### a. Name one thing the AI agent got wrong. How did you notice?

Early in scoping the DB schema, the agent's first instinct was to make `Disagreement` the primary persisted artifact — i.e. run the comparison once at import time and store the results, with the API just reading that table. I noticed this would go stale the moment `import_data` re-ran (a disagreement that got fixed upstream would linger in the table until someone remembered to re-run a separate "recompute" step), which is a real bug class in reconciliation tools. I pushed back and we switched to computing disagreements fresh on every API request instead, keeping the `Disagreement` model in the schema for future use but not populating it in this build.

### b. Which part of your submission are you least confident about, and why?

The `REC-1055` handling. It has two System B entries whose values sum exactly to System A's total, labeled "Entry part 2 of 2" — which reads like a legitimate split, not an error. I chose to still flag it as `DUPLICATE_IN_B` (with a note in the detail text) rather than silently special-casing sum-matching pairs out of the results, because I'd rather over-flag one ambiguous case for a human to look at than write a rule that could hide a genuine double-billing bug in real data that just happens to sum correctly by coincidence. But I could see an argument for a fifth explicit category (`SPLIT_ENTRY`) instead, and I'm not fully confident `DUPLICATE_IN_B` is the right bucket for it.

### c. If you had a second day, what would you fix first?

I'd add a `SPLIT_ENTRY` category instead of overloading `DUPLICATE_IN_B` for the `REC-1055` case, and I'd add an admin or summary view over the `ImportIssue` table (right now it's genuinely there, capturing every dirty row correctly, but you have to go into `/admin/` or the ORM to see it — it deserves its own place in the UI, since "what got flagged during import" is arguably as important as "what disagreed between systems.")