# DECISIONS

## Architectural and Technical Decisions

### 1. Disagreement computation: API request vs. stored results
**Decision:** Compute disagreements fresh on every API request  
**Alternative:** Run comparison once at import time and store results  
**Reasoning:** Stored results would go stale if data is re-imported; computing on demand ensures accuracy without requiring manual recompute steps.

### 2. Record reference field: String vs. foreign key
**Decision:** String field for record_ref in SystemBEntry  
**Alternative:** Foreign key to SystemARecord  
**Reasoning:** Dirty data means some references won't match existing records; string field allows import with proper error handling instead of import failures.

### 3. REC-1055 duplicate handling: Flag as duplicate vs. create split category
**Decision:** Flag as DUPLICATE_ENTRY with detail note  
**Alternative:** Create new SPLIT_ENTRY category  
**Reasoning:** Over-flagging one ambiguous case is safer than writing rules that could hide genuine double-billing bugs that happen to sum correctly.

### 4. Frontend: React vs. plain HTML/JS
**Decision:** React with Vite  
**Alternative:** Plain HTML/JavaScript  
**Reasoning:** React provides better state management for complex filtering/sorting and easier component organization for future features.

### 5. Styling: Dark theme vs. light theme
**Decision:** Dark theme with grey/black/white palette  
**Alternative:** Light theme with colors  
**Reasoning:** Dark theme reduces eye strain for data analysis tasks and provides modern, professional appearance.

### 6. Testing: Django tests vs. external test framework
**Decision:** Django's built-in test framework  
**Alternative:** pytest or external framework  
**Reasoning:** Django's built-in tests are sufficient for this scope and avoid additional dependency complexity.

### 7. Database: SQLite vs. PostgreSQL
**Decision:** SQLite for development  
**Alternative:** PostgreSQL for production  
**Reasoning:** 120 rows per system makes SQLite more than sufficient while avoiding database setup complexity for evaluation.

### 8. Import issues: Separate model vs. logging only
**Decision:** ImportIssue model to capture all dirty rows  
**Alternative:** Only log issues to console  
**Reasoning:** Capturing issues in database enables inspection and analysis without losing information about data quality problems.