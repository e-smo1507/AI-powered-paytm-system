## Bug Fixes Summary

### Fixed
1. **Devanagari numeral `characters.characters` crash in `nlu.py`** — Python 3.13 doesn't have `characters.characters` attribute
2. **Stray comma in `frontend/index.html`** — broken string literal
3. **Frontend `toLocaleString` call crash** — calling toLocaleString with options object crashes in edge environments

### Running Tests
```bash
python -m backend.test_journeys
```

### Architecture
- Backend: FastAPI (backend folder)
- Frontend: Static HTML/JS (frontend folder)
- Tests: `backend/test_journeys.py`
