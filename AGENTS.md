# BoviCare project instructions

- Project: BoviCare, an AI cattle health triage and veterinary consultation platform for India. The frontend uses React, Vite, and Tailwind CSS v3. The backend uses FastAPI and SQLAlchemy. Roles are farmer, doctor, and admin. Languages are English, Hindi, and Marathi.
- Build on the existing code. Do not rewrite working features. Do not change API contracts without stating the change. Never loosen validation to hide an error.
- Keep the four model outputs separate. Never average them.
- Enforce roles on the backend. Doctor `clinical_notes` must never appear in any farmer-facing response.
- Every visible string must exist in English, Hindi, and Marathi.
- Do not include medicine names or doses in generated content.
- Never read, print, or commit `.env` files or secrets. `SECRET_KEY` must be at least 32 bytes.
- Brand colors: primary `#166534`, accent `#CA8A04`, background `#F7F5EF`. Use risk colors only for risk and status, always with an icon and text.
- Before finishing a task, run the build, lint, tests, and a backend start check. Report a short **Test | Result** table.
