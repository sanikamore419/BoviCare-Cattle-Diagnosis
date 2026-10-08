# BoviCare AI

## Intelligent Cattle Diagnosis Platform

BoviCare AI is a full-stack AI-powered veterinary decision-support platform designed to help cattle farmers and veterinarians with early disease assessment, cattle health management, remote veterinary review, and diagnostic reporting.

The system combines symptom-based machine learning, milk-parameter analysis, and image-based disease classification in one platform.

> **Important:** BoviCare AI provides AI-based decision support and preliminary predictions. It is not a replacement for professional veterinary diagnosis or treatment.

## Backend database migrations

From the `backend/` directory, apply database schema changes before starting the API:

```powershell
python -m alembic upgrade head
```

The API does not create or alter database tables at startup. Production deployments must apply migrations as a release step before starting application workers.

For an existing pre-Alembic development database, first back it up and verify that it matches the `0001_baseline` schema. Stamp only that verified database with the baseline, then run `python -m alembic upgrade head`. Do not stamp an unknown or mismatched schema.

---

## Project Overview

In rural and semi-urban areas, farmers may face difficulties in accessing veterinary services quickly. Symptoms may be incomplete or difficult to communicate, and early signs of disease can sometimes be missed.

BoviCare AI provides a structured digital workflow:

```text
Farmer
   ↓
Cattle Information
   ↓
Symptoms / Milk Parameters / Image
   ↓
AI Analysis
   ↓
Disease Predictions
   ↓
Risk Assessment
   ↓
Diagnostic Report
   ↓
Veterinary Review
