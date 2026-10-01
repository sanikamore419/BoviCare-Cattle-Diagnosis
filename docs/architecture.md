# Architecture notes

The React client calls FastAPI through `/api/v1`. SQLAlchemy persists users and clinical cases. `PredictionService` isolates case handling from a future validated ML integration. A veterinarian should review cases before treatment decisions.
