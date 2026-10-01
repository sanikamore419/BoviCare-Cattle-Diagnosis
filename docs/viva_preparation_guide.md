# BoviCare AI: Viva Preparation Guide

## Evidence rule
This guide is based on the current repository implementation. Status labels mean:

- **IMPLEMENTED**: present in the source and exercised by the verification flow.
- **PARTIALLY IMPLEMENTED**: present in some layer, but not complete or not persisted.
- **FUTURE SCOPE**: a reasonable extension, not a current feature.
- **LIMITATION**: an important constraint or risk in the current implementation.

The safest viva wording is: "The system provides AI-assisted decision support. It does not independently confirm a clinical diagnosis or replace a veterinarian."

## Important corrections before the viva

1. The active prediction services are under `backend/ml`. The root `ml_model/predictor.py` is a separate placeholder interface and is used by the older `PredictionService` triage path, not by the main `/api/v1/predictions` ML routing path.
2. Models A-D are independent. Their probabilities are never averaged or merged. The router only derives a combined **risk label** by taking the highest individual risk level when Models A and B both run.
3. Models C and D are called through `/api/v1/predictions/image`; they are not automatically called by `route_prediction`.
4. Exact stored metrics exist for Models C and D. Model A and Model B training scripts calculate metrics, but the repository does not store their printed final metric values in metadata. Do not invent A/B accuracy, F1, or ROC-AUC values.
5. Recharts is listed as a dependency, but no current frontend source uses a Recharts chart.
6. The doctor page has `Confirm diagnosis` and `Treatment / advice` inputs, but those inputs are not sent by the review request. Only veterinarian notes and review status are persisted.
7. Notifications are database notification events with mock/queued/failed status logic. There is no implemented email or SMS delivery client.

# Part 1 - 2-minute project introduction

## 30-second version

"My project is BoviCare AI, an intelligent cattle diagnosis platform. It allows a farmer to create a cattle profile, submit symptoms, optional milk measurements, and an optional image. The FastAPI backend stores the case and routes the available inputs to separate prediction models. Results include disease labels, probabilities, and an indicative risk level. A veterinary doctor can view cases, see the model results, add notes, mark a case as reviewed, and download a PDF report. The system is decision support only, so the veterinarian remains responsible for clinical confirmation."

## 1-minute version

"BoviCare AI addresses the difficulty of getting an early cattle health assessment, especially when a farmer cannot immediately consult a veterinarian. The main users are farmers and veterinary doctors. The React and Vite frontend provides separate farmer and veterinary workspaces. The FastAPI backend handles authentication, cattle records, cases, predictions, private images, notifications, reports, and review workflow. There are four independent models: a general symptom classifier, a mastitis model using milk parameters, a general cattle image classifier, and a lumpy-skin image specialist. Depending on the input, the backend runs the appropriate model and stores each result separately. The expected benefit is earlier attention and better information sharing, not automatic treatment."

## 2-minute version

"My project is BoviCare AI: Intelligent Cattle Diagnosis Platform. The problem is that cattle symptoms may be noticed by a farmer before a veterinarian is available, and the information may not be recorded in a structured way. The goal is to provide a preliminary, organized assessment and make remote veterinary review easier.

There are two users. A farmer can register, manage cattle, create a clinical case, select symptoms, enter temperature and optional milk measurements, upload an image, view prediction results, and download a report. A veterinary doctor can access the case list, filter cases, inspect clinical information and stored model results, view a private image, add veterinarian notes, change review status, and download the report.

The frontend is a React single-page application built with Vite, React Router, Tailwind CSS, Axios, and Lucide React. The backend is a Python FastAPI REST API served by Uvicorn. SQLAlchemy persists users, cattle, cases, prediction rows, images, and notification logs. SQLite is the local default and PostgreSQL is supported by configuration. Authentication uses JWT access tokens and Argon2 password hashing.

The ML layer has four independent models. Model A uses symptom features for general cattle disease classification and returns up to five ranked results. Model B is a mastitis specialist using six milk parameters. Model C is a seven-class EfficientNet-B0 image classifier for HEALTHY, LSD, RINGWORM, FMD, IBK, PEDICULOSIS, and DERMATOPHILOSIS. Model D remains a two-class MobileNetV2 specialist for Lumpy Skin and Normal Skin. The system does not combine their probabilities. It displays each model independently, and uses the highest risk band only for a general case risk label where applicable.

The normal workflow is: authenticate, create or select cattle, create a case, send the available input to the suitable model endpoint, persist the output, create a high-risk notification event when appropriate, show the results, allow veterinarian review, and generate a PDF report. The benefit is faster preliminary triage and better communication. It is not a clinically validated replacement for a veterinarian."

# Part 2 - Project overview questions

1. **HIGH PRIORITY - What is BoviCare AI?**
   - **Answer:** It is a web platform for AI-assisted cattle health assessment, case persistence, and veterinary review.
   - **Deeper:** React calls FastAPI endpoints. SQLAlchemy stores domain data and separate prediction results; model services perform inference.
2. **Why did you choose this project?**
   - **Answer:** Cattle health problems can need early attention, while veterinary access may be delayed.
   - **Deeper:** The system structures farmer observations and makes them available to a doctor; it is not a clinical replacement.
3. **What problem are you solving?**
   - **Answer:** Unstructured symptom/image submission and delayed sharing of information with veterinarians.
   - **Deeper:** The API links cattle, cases, predictions, images, review notes, notification logs, and reports.
4. **Who are the users?**
   - **Answer:** Farmers and veterinary doctors.
   - **Deeper:** `farmer` and `doctor` roles are checked by backend dependencies and frontend protected routes.
5. **What is the main objective?**
   - **Answer:** Give a preliminary risk-oriented assessment and support remote veterinary review.
   - **Deeper:** The output contains probabilities and confidence-style risk bands, explicitly marked as non-clinical.
6. **What makes the project different?**
   - **Answer:** It accepts symptoms, milk data, and images and keeps the corresponding model outputs separate.
   - **Deeper:** Models are specialized by input type instead of forcing unrelated inputs into one probability score.
7. **What is the input?**
   - **Answer:** Cattle details, symptoms, optional temperature, six optional milk fields, and an optional image.
   - **Deeper:** Pydantic schemas validate ranges and image storage validates MIME type, size, and image content.
8. **What is the output?**
   - **Answer:** Disease labels or mastitis condition, probabilities, ranks where available, risk levels, and a disclaimer.
   - **Deeper:** Results are persisted in `prediction_results` with model name, version, rank, label, probability, and risk.
9. **What is the workflow?**
   - **Answer:** Login, select cattle, create case, submit inputs, view results, request/review veterinary assessment, download report.
   - **Deeper:** The frontend calls `/cases/triage`, `/predictions`, and `/predictions/image`, then fetches persisted results.
10. **What are the major modules?**
    - **Answer:** Authentication, cattle management, cases, prediction services, image storage, reports, notifications, and doctor review.
    - **Deeper:** The backend separates routers, schemas, models, and services.
11. **What are the advantages?**
    - **Answer:** Structured records, multiple input modalities, role-based access, persisted history, and remote review.
    - **Deeper:** The final verification exercised ownership, all four model groups, private images, PDF content, and review flow.
12. **What are the limitations?**
    - **Answer:** Dataset dependence, no clinical validation, indicative thresholds, and no real external notification delivery.
    - **Deeper:** The code itself labels risk as model confidence and includes a veterinarian disclaimer.
13. **What is future scope?**
    - **Answer:** More clinical data, IoT integration, mobile access, multilingual support, real providers, deployment, and retraining.
    - **Deeper:** None of those should be described as currently implemented.
14. **Why is AI required?**
    - **Answer:** It can identify patterns in symptoms, milk measurements, and images and provide a ranked preliminary result.
    - **Deeper:** Model A/B use scikit-learn classifiers; Models C/D use transfer learning with MobileNetV2.
15. **Why cattle disease diagnosis?**
    - **Answer:** It is a practical domain where early observation and veterinary collaboration can be valuable.
    - **Deeper:** The implementation includes general disease, mastitis, and lumpy-skin-specific paths.
16. **Can the system replace a veterinarian?**
    - **Answer:** No. It is decision support and the report/API explicitly require qualified veterinary confirmation.
    - **Deeper:** The doctor review endpoint persists notes and status, but treatment is not automatically generated.
17. **Is the result a diagnosis?**
    - **Answer:** No. It is a prediction or preliminary risk assessment.
    - **Deeper:** Probability is model output, not clinical disease probability.
18. **What is persisted?**
    - **Answer:** Users, cattle, cases, prediction rows, case-image metadata, and notification logs.
    - **Deeper:** Image bytes are stored outside the database; the database stores a generated filename and metadata.
19. **Does the system keep history?**
    - **Answer:** Yes, cases and prediction rows remain available through authenticated case endpoints.
    - **Deeper:** `/cases/{case_id}/predictions` groups rows by model name without merging them.
20. **What happens without valid input?**
    - **Answer:** The prediction schema rejects a request without symptoms or milk data with HTTP 422; the image path separately needs a valid upload.
    - **Deeper:** The frontend also prevents submission when there is no symptom, milk data, or image.
21. **What happens with only symptoms?**
    - **Answer:** Model A runs.
    - **Deeper:** It creates a binary symptom vector and returns up to five non-zero ranked classes.
22. **What happens with only milk data?**
    - **Answer:** Model B runs.
    - **Deeper:** It predicts `Mastitis` or `No Mastitis` using six named features.
23. **What happens with both?**
    - **Answer:** Models A and B run independently.
    - **Deeper:** Their result objects remain separate; only the highest risk label is selected for the combined risk field.
24. **What happens with only an image?**
    - **Answer:** The image endpoint runs either Model C or Model D according to the `model` form field.
    - **Deeper:** The current frontend creates a case first when submitting a new diagnosis, then uploads the image linked to that case.
25. **What is the biggest strength?**
    - **Answer:** It connects multimodal prediction with persistence and human veterinary review.
    - **Deeper:** The end-to-end verification passed 26 of 26 checks, including all four model result groups.
26. **What is the biggest weakness?**
    - **Answer:** The model outputs and thresholds are not clinically validated in this repository.
    - **Deeper:** Dataset test metrics are not evidence of real-world clinical accuracy.

# Part 3 - System architecture

```text
React + Vite frontend
        |
        | Axios REST calls
        v
FastAPI + Uvicorn
        |
        +-- JWT authentication and role checks
        +-- Routers, Pydantic schemas, business rules
        +-- SQLAlchemy / SQLite or PostgreSQL
        +-- ML prediction services
        +-- Private image storage
        +-- ReportLab PDF and notification logs
        v
Persisted prediction results and veterinarian review
```

1. **Explain the architecture.** The React SPA collects data and calls FastAPI. FastAPI validates/authenticates requests, routes business operations, invokes ML services, persists results, and exposes reports/review endpoints.
2. **Why React?** Components and client-side routing support separate dashboards and reusable forms. It is implemented with React Router and React state/effects.
3. **Why FastAPI?** It provides typed request validation through Pydantic, automatic OpenAPI documentation, dependency injection, and async file-upload support.
4. **Why REST?** Resources such as users, cattle, cases, predictions, images, and reports map naturally to HTTP endpoints and can be consumed by a web or future mobile client.
5. **Why separate frontend/backend?** It separates presentation from authentication, persistence, and ML logic. The same backend can support another client later.
6. **How does the frontend communicate?** Axios uses `http://localhost:8000/api/v1` by default and adds a Bearer token from local storage.
7. **What is an endpoint?** A URL plus an HTTP method and contract, such as `POST /api/v1/predictions`.
8. **What happens after Submit Diagnosis?** The frontend creates a triage case, calls symptom/milk prediction when applicable, uploads the image when applicable, and navigates to the result view.
9. **Why modular architecture?** Routers handle HTTP, schemas validation, models persistence, and services reusable domain operations.
10. **How can IoT be added?** **Future scope:** add an authenticated sensor-ingestion endpoint and map sensor readings to cattle/cases; no IoT endpoint exists now.

# Part 4 - Frontend viva

## Key concepts

| Concept | Definition | Use in BoviCare | Why |
|---|---|---|---|
| React component | Reusable UI function | Pages and components such as `Dashboard`, `NewCase`, `AppShell` | Separates screens and repeated UI |
| State | Data that changes UI | Form fields, loading, errors, cattle list, predictions | Makes forms and API results interactive |
| Props | Inputs passed to a component | `ProtectedRoute`, `Card`, `Badge`, form callbacks | Reuse and configuration |
| React Router | Client-side URL routing | Landing, farmer routes, veterinary routes | SPA navigation without full reload |
| Axios | HTTP client | API calls and protected PDF/image requests | Central base URL and auth interceptor |
| Tailwind CSS | Utility CSS framework | Layout, colors, responsive classes | Consistent responsive UI |
| Context | Shared React state | `AuthContext` stores user/session actions | Avoids passing auth through every page |
| Recharts | Chart library | Dependency only; no current chart usage found | Do not claim implemented charts |

## Questions

1. **How is routing implemented?** `App.jsx` uses `Routes` and `Route`, with farmer and doctor wrappers around protected pages.
2. **How are protected routes enforced?** `ProtectedRoute` checks loading, user existence, and allowed role; unauthorized users are redirected.
3. **Is frontend protection enough?** No. It is only user experience protection; backend dependencies enforce authorization.
4. **How is auth state stored?** User and JWT are stored in `localStorage`; startup calls `/auth/me` to validate the token.
5. **How does logout work?** It removes `bovicare_token` and `bovicare_user` and clears context state.
6. **How are expired tokens handled?** Axios removes stored auth data on HTTP 401 and dispatches `bovicare:auth-expired`.
7. **How does the form work?** `NewCase` stores cattle fields, selected symptoms, milk fields, image file, and model choice in React state.
8. **How are symptoms selected?** Buttons toggle strings in a symptoms array.
9. **How is milk data sent?** The six fields are converted to numbers and sent as `milk_data`.
10. **How are images sent?** A `FormData` object includes `file`, model, and optional cattle/case IDs.
11. **How is loading represented?** Pages use loading state and components such as `LoadingState`; submit buttons show a spinner/text.
12. **How are errors represented?** Axios error details are shown in `ErrorAlert` or local messages.
13. **How does the dashboard get data?** It calls `/cases` and `/cattle` with `Promise.all`.
14. **How does the diagnosis page get persistent results?** It calls `/cases/{case_id}/predictions`; router state is used as an immediate fallback.
15. **How is the PDF downloaded?** Axios requests a blob, creates an object URL, and clicks a temporary download anchor.
16. **How does the doctor dashboard filter cases?** It filters loaded cases in client state by text, risk, and status.
17. **What responsive behavior exists?** Tailwind responsive classes and a mobile navigation drawer are used.
18. **Are charts implemented?** No current source uses Recharts. The package is installed, but chart-based analytics should be called future/unused.
19. **Are doctor treatment fields persisted?** No. The visible treatment/advice and confirm-diagnosis inputs are not included in the PUT payload.
20. **What happens if the API is down?** Pages show an error message such as “Could not reach the API”; the frontend build itself can still succeed.
21. **Does the frontend independently calculate medical risk?** It colors probability bars at 40% and 70%, but the authoritative prediction/risk values come from the backend.
22. **How does the UI communicate limitations?** It displays AI decision-support disclaimers and veterinarian-confirmation messages.

# Part 5 - Backend viva

## Actual API inventory

| Endpoint | Method | Purpose | Auth |
|---|---:|---|---|
| `/health` | GET | Health check | None |
| `/api/auth/register` | POST | Create farmer/doctor account in development/test | None |
| `/api/auth/login` | POST | Return bearer JWT and user | None |
| `/api/auth/me` | GET | Return current user | Authenticated |
| `/api/v1/auth/register` | POST | Same auth router under v1 prefix | None |
| `/api/v1/auth/login` | POST | Same login route under v1 prefix | None |
| `/api/v1/auth/me` | GET | Same current-user route under v1 | Authenticated |
| `/api/v1/cattle` | GET | List farmer-owned cattle or all cattle for doctor | Authenticated |
| `/api/v1/cattle` | POST | Create cattle | Farmer |
| `/api/v1/cattle/{cattle_id}` | GET | Read cattle | Authenticated; farmer owner check |
| `/api/v1/cattle/{cattle_id}` | PUT | Update cattle | Farmer owner |
| `/api/v1/cattle/{cattle_id}` | DELETE | Delete cattle | Farmer owner |
| `/api/v1/cases/triage` | POST | Create farmer clinical case and preliminary triage | Farmer |
| `/api/v1/cases` | GET | List own farmer cases or all cases for doctor | Authenticated |
| `/api/v1/cases/{case_id}` | GET | Read case | Authenticated; farmer owner check |
| `/api/v1/cases/{case_id}/report` | GET | Stream PDF report | Authenticated; owner/doctor |
| `/api/v1/cases/{case_id}/image` | GET | Stream private stored image | Authenticated; owner/doctor |
| `/api/v1/cases/{case_id}/notifications` | GET | Read notification logs | Authenticated; owner/doctor |
| `/api/v1/cases/{case_id}/predictions` | GET | Read model results grouped independently | Authenticated; owner/doctor |
| `/api/v1/cases/{case_id}/review` | PUT | Save doctor notes/status | Doctor |
| `/api/v1/predictions` | POST | Run Models A/B from symptoms/milk data | Authenticated |
| `/api/v1/predictions/image` | POST | Run Model C or D from multipart image | Authenticated |

## Questions

1. **What is FastAPI?** A Python web framework used here to define typed REST endpoints and OpenAPI documentation.
2. **What is Uvicorn?** The ASGI server used to run `app.main:app`.
3. **What is a router?** A module grouping related endpoints; the project has auth, cattle, cases, predictions, and health routers.
4. **What are schemas?** Pydantic request/response models that validate and document API data.
5. **What are models?** SQLAlchemy classes mapping Python objects to database tables.
6. **What are services?** Focused modules for prediction handling, images, notifications, and reports.
7. **What is dependency injection here?** FastAPI `Depends` supplies database sessions and current-user/role checks.
8. **What is `POST /cases/triage`?** A farmer-only case creation endpoint. It validates cattle ownership, runs the older preliminary triage service when symptoms exist, persists the case, and logs high risk.
9. **What is `POST /predictions`?** An authenticated endpoint that validates case/cattle ownership, routes symptoms to A and milk data to B, stores each prediction row, and returns separate result objects.
10. **What is `POST /predictions/image`?** An authenticated multipart endpoint validating an image and running the selected cattle or lumpy specialist model.
11. **What is GET case predictions?** It retrieves rows and groups them by `model_name`; it does not calculate a merged probability.
12. **What are GET/POST/PUT/DELETE examples?** GET reads, POST creates/runs operations, PUT updates cattle/review, DELETE removes cattle.
13. **What is HTTP 201?** Successful resource creation, used for registration, cattle creation, and triage case creation.
14. **What is HTTP 401?** Missing, invalid, or expired authentication.
15. **What is HTTP 403?** Authenticated but not authorized, such as a farmer accessing another farmer's case.
16. **What is HTTP 404?** Requested case, cattle, image, or resource does not exist.
17. **What is HTTP 409?** Duplicate email registration.
18. **What is HTTP 413?** Image exceeds the 10 MB limit.
19. **What is HTTP 415?** Unsupported MIME type or invalid image content.
20. **What is HTTP 422?** Validation or business input error, including no prediction input or mismatched cattle/case.
21. **What is HTTP 503?** A required model is unavailable.
22. **How is validation done?** Pydantic fields constrain types, lengths, literals, and numeric ranges.
23. **What is CORS?** Browser cross-origin access control. FastAPI middleware uses configured frontend origins and allows methods/headers.
24. **How is file upload handled?** `UploadFile` is read, MIME-checked, size-limited, opened and verified with Pillow, then passed to the model.
25. **How is an image stored?** A UUID filename is written under configured `upload_dir`; the database stores metadata.
26. **How is path traversal prevented?** `image_path` resolves the candidate and requires its parent to equal the upload root.
27. **How are PDFs generated?** ReportLab draws a PDF from persisted case, prediction, review, and notification data and streams it as `application/pdf`.
28. **How are notifications generated?** High-risk case creation or high-risk prediction calls `create_high_risk_notification`.
29. **How is duplicate notification prevented?** The service checks case, notification type, and model in the stored event payload.
30. **What is not implemented in notifications?** No actual email/SMS client; status is mock, queued, or failed based on configuration logic.
31. **What happens on database failure after image save?** The image file is removed, the session rolls back, and the exception is raised.
32. **Why use a service layer?** It isolates prediction, storage, report, and notification logic from route functions.
33. **What is the current default database?** SQLite at `sqlite:///./bovicare.db`; PostgreSQL can be selected with `DATABASE_URL`.
34. **What is startup behavior?** Tables are created with SQLAlchemy, and a SQLite compatibility migration adds `cattle_id` to old clinical case tables if needed.

# Part 6 - Database viva

## Tables and relationships

- `users`: identity, email, password hash, role.
- `cattle`: farmer-owned animal profile; `farmer_id -> users.id`.
- `clinical_cases`: case information; `owner_id -> users.id`, optional `cattle_id -> cattle.id`.
- `prediction_results`: one row per model prediction/rank; optional case/cattle and required owner references.
- `case_images`: one stored image per case because `case_id` is unique; links case, cattle, and owner.
- `notification_logs`: high-risk notification events linked to a case.

The source defines foreign keys but does not define SQLAlchemy `relationship()` attributes. Relationships are represented through foreign-key columns and explicit queries.

## Speakable ER explanation

"A user can be a farmer or doctor. A farmer can own many cattle and create many clinical cases. A case can optionally refer to one cattle record. A case can have many prediction result rows because each model and rank is stored separately. A case can have one stored image in the current schema. A case can have notification log entries. Doctors access cases for review, but the doctor role is not stored as a foreign key on the case."

## Questions

1. **Why is a database required?** To retain accounts, cattle profiles, cases, predictions, image metadata, notification events, and review notes.
2. **Why SQLAlchemy?** It maps Python classes to tables and supports SQLite/PostgreSQL configuration.
3. **Why SQLite?** It is simple and zero-configuration for local development.
4. **Why PostgreSQL readiness?** A production deployment can use a server database through `DATABASE_URL` and psycopg.
5. **What is a primary key?** A unique identifier; each current table uses an integer `id`.
6. **What is a foreign key?** A reference to another table's key, such as `owner_id` to `users.id`.
7. **What is the users table?** It stores full name, unique indexed email, password hash, role, and creation time.
8. **What roles exist?** The schema permits `farmer` and `doctor`.
9. **What does cattle store?** Tag number, optional name/breed/date of birth/weight, sex, farmer owner, and timestamps.
10. **What does a case store?** Tag, optional cattle link, breed, age, temperature, JSON-encoded symptoms, preliminary prediction, risk, status, notes, and time.
11. **Why are symptoms JSON text?** The current implementation serializes the symptom list into a text column and deserializes it for responses.
12. **What does prediction storage contain?** Model name/version, rank, disease label, probability, risk, owner, optional case/cattle, and timestamp.
13. **Why multiple prediction rows?** General and image models may return ranked lists; separate rows preserve model identity and rank.
14. **How is Model B stored?** One rank-1 row with `mastitis_specialist` and its condition/probability.
15. **How is image metadata stored?** Case ID, cattle ID, owner ID, generated filename, MIME type, and timestamp.
16. **Why store image bytes outside the database?** The database keeps relational metadata while filesystem storage handles the binary file.
17. **How is image uniqueness modeled?** `case_id` is unique in `case_images`, so the current case has at most one stored image record.
18. **What is notification storage?** Case, type, target role, status, JSON event payload, and timestamp.
19. **Where are veterinarian notes stored?** `clinical_cases.veterinarian_notes`.
20. **Where is review status stored?** `clinical_cases.status`, initially `pending_review` and set through the doctor review endpoint.
21. **Are SQLAlchemy relationships declared?** No explicit ORM `relationship()` fields are defined; foreign keys and queries are used.
22. **What happens when a case is deleted?** No case-delete endpoint is implemented, so cascade behavior is not an exposed workflow.
23. **What happens when cattle is deleted?** The farmer delete endpoint deletes the cattle row; the repository does not define database cascade configuration.
24. **How are old SQLite databases handled?** Startup checks for a missing `cattle_id` column and adds it.
25. **What is an index?** A structure for faster lookup; email, owner IDs, tags, case IDs, and related columns have indexes where declared.
26. **What is the database limitation?** There is no migration framework or explicit ORM relationship layer in the current repository.

# Part 7 - Authentication and security

1. **Authentication vs authorization?** Authentication proves identity; authorization checks what that identity may do.
2. **How is authentication implemented?** Login verifies a stored password hash and returns a JWT bearer token.
3. **How is authorization implemented?** `require_roles("farmer")` or `require_roles("doctor")` and explicit ownership checks.
4. **What is JWT?** A signed token carrying the user ID subject and expiration.
5. **What is in the token?** `sub` is the user ID and `exp` is the expiry; role is read from the database, not trusted from the token.
6. **How is a password stored?** As an Argon2-derived hash using `pwdlib`, never as plaintext.
7. **What is a salt?** Random data used by password hashing so equal passwords do not produce the same stored hash.
8. **What is the farmer role?** It can manage its own cattle, create triage cases, and access its own records.
9. **What is the doctor role?** It can list all cattle/cases for review, run predictions, view permitted case data, and update review notes/status.
10. **Can a doctor create cattle?** No; cattle creation is farmer-only.
11. **Can a doctor update/delete cattle?** No; those endpoints require farmer role.
12. **Can a doctor review?** Yes; `/cases/{id}/review` requires doctor role.
13. **What if a farmer accesses another farmer's case?** The backend returns 403 through `ensure_case_access`.
14. **What if a farmer accesses another farmer's cattle?** The backend returns 403 through `ensure_owner`.
15. **What if a farmer uses another farmer's cattle in prediction?** The backend returns 403.
16. **What if a farmer calls doctor review?** The role guard returns 403.
17. **What if an unauthenticated user calls prediction?** `get_current_user` returns 401.
18. **What if a token is invalid/expired?** JWT decoding fails and the API returns 401.
19. **Why cannot the frontend be trusted?** A user can bypass JavaScript; authorization must be enforced at the API and database-access boundary.
20. **What does CORS protect?** It controls browser origins; it is not authentication or authorization.
21. **How are images private?** There is no public static mount; the image is returned only by an authenticated case endpoint after access checks.
22. **How is traversal blocked?** Stored filenames are generated UUIDs and resolved paths must remain inside the upload root.
23. **What image limits exist?** JPEG, PNG, WEBP, and BMP; maximum 10 MB; Pillow verifies actual image content.
24. **What are environment variables for?** Database URL, secret key, frontend origins, upload directory, token duration, and notification settings.
25. **What is the production secret rule?** Startup rejects production/prod mode if the default development secret remains.
26. **What is not a complete production security solution?** SQLite/local storage, development registration of doctor accounts, no rate limiting, and no external identity provider are not production hardening.
27. **Can doctors self-register?** In development/test they can; non-development registration of doctor accounts is rejected with 403.
28. **Does frontend localStorage remove all token risk?** No. It is convenient for this client but requires normal browser/XSS hardening in production.
29. **What about sensitive data in notifications?** The event payload records case/model/risk/disease information and the verification checks that farmer email/phone are not included.
30. **What security test evidence exists?** The final script passed unauthenticated, cross-farmer, farmer-review, image-access, and invalid-reference checks.

# Part 8 - Machine learning overview

## Model A - general symptom classifier

- **Purpose:** General cattle disease classification from symptoms.
- **Input:** Symptom names matching feature columns.
- **Dataset:** `Training.csv` from the referenced GitHub dataset: 2,044 training rows, 93 binary symptom features, 26 disease classes; `Testing.csv` has 26 rows, one per class.
- **Algorithm:** Random Forest selected by stratified 5-fold macro-F1 comparison against Logistic Regression and Gradient Boosting.
- **Preprocessing:** Lowercase/trim/space-to-underscore symptom names; build a binary feature vector in the saved feature-column order; LabelEncoder for the target.
- **Output:** Up to five ranked non-zero disease probabilities.
- **Risk:** top probability >= 0.70 high, >= 0.40 moderate, otherwise low.
- **Metrics:** Training script computes held-out accuracy and macro F1. Exact printed A values are not stored in the repository metadata; do not quote a number unless you rerun training and record it.
- **Limitation:** The held-out test has only 26 rows and is dataset-specific.

## Model B - mastitis specialist

- **Purpose:** Mastitis classification from milk measurements.
- **Input:** Milk_Temperature, Milk_pH, Milk_Conductivity, Somatic_Cell_Count, Milk_Yield, Clotting.
- **Dataset:** local `cow_milk_mastitis_dataset.csv`, 800 rows; 631 negative and 169 positive; target `class1`.
- **Algorithm:** Random Forest and Logistic Regression compared using stratified 5-fold macro F1. The selected pipeline includes StandardScaler and a Random Forest with class balancing if RF wins.
- **Output:** `Mastitis` or `No Mastitis`, positive-class probability, risk.
- **Metrics:** The script computes accuracy, macro F1, and ROC-AUC on a stratified 20% held-out test split. Exact output values are not stored in metadata; do not invent them.
- **Why separate:** Milk measurements represent a specialist signal and are not symptom feature columns.

## Model C - general cattle image classifier

- **Architecture:** EfficientNet-B0, PyTorch; the supplied checkpoint has a seven-output classification head.
- **Checkpoint:** `backend/ml/final_model/bovicare_efficientnet_b0.pth`.
- **Classes and output order:** `HEALTHY`, `LSD`, `RINGWORM`, `FMD`, `IBK`, `PEDICULOSIS`, `DERMATOPHILOSIS`.
- **Input/preprocessing:** RGB image resized to 224x224, converted to a tensor, then normalized with ImageNet mean `[0.485, 0.456, 0.406]` and standard deviation `[0.229, 0.224, 0.225]`.
- **Inference output:** logits are converted to per-class softmax probabilities and returned in rank order. The calibration summary reports evaluation errors; it does not specify a runtime calibration transform.
- **Limitation:** Supplied evaluation metrics are not runtime prediction results and do not establish clinical validity.

## Model D - lumpy skin specialist

- **Purpose:** Specialist visual classification of Lumpy Skin versus Normal Skin.
- **Dataset:** referenced lumpy skin dataset, 1,024 images: Lumpy Skin 324 and Normal Skin 700.
- **Classes:** `Lumpy Skin`, `Normal Skin`.
- **Architecture/preprocessing/training:** MobileNetV2 transfer learning, frozen features, 224x224 RGB, ImageNet normalization, augmentation, class weights, stratified 70/15/15 split, early stopping.
- **Stored results:** test accuracy 0.8961; macro F1 0.8775; ROC-AUC 0.9351.
- **Limitation:** Class distribution and dataset conditions may differ from field images.

# Part 9 - Model A deep viva

1. What is the target? `prognosis`, encoded with LabelEncoder.
2. What is the feature representation? A 93-dimensional binary symptom vector.
3. How are unknown symptoms handled? They are silently ignored and therefore become zero features.
4. What is multi-class classification? One input is assigned among multiple disease classes.
5. Why Random Forest? It handles binary feature matrices, is robust, and supplies probabilities.
6. What models were compared? Random Forest, Logistic Regression, Gradient Boosting.
7. How was selection done? Stratified 5-fold CV using macro F1.
8. Why macro F1? It gives each class equal importance despite class imbalance.
9. What is the final training set? The selected classifier is fit on all 2,044 training rows.
10. What is the test set? 26 rows, one per class according to the script.
11. What is the small-test limitation? One sample per class makes accuracy/F1 unstable and not representative of deployment.
12. What is top-5? Probabilities are sorted descending and up to five non-zero classes are returned.
13. Are top-5 probabilities combined? No, they remain individual class probabilities.
14. Why probability? `predict_proba` supports a ranked uncertainty-style output.
15. What is risk? An indicative band based only on the top model probability.
16. Is risk clinical? No; code comments explicitly say it needs veterinary validation.
17. What artifacts are saved? Model, label encoder, and feature columns as joblib files.
18. Why save feature columns? Inference must create the vector in the same order as training.
19. What if symptoms have spaces? Inference replaces spaces with underscores before matching.
20. What if a disease is outside 26 classes? The model cannot reliably identify an unseen class.
21. Is the model deep learning? No, it is a scikit-learn Random Forest.
22. Is cross-validation the final test? No. CV selects the algorithm; the held-out test evaluates the selected model.
23. What metric is available? The script calculates accuracy, macro F1, and a per-class report.
24. What number should you quote? No A metric number is persisted in this repository; say that honestly.
25. What is the main Model A limitation? Small held-out set and dataset-dependent generalization.

# Part 10 - Model B deep viva

1. What disease does it target? Mastitis.
2. Is it binary? Yes: No Mastitis versus Mastitis.
3. What are the six features? Milk temperature, pH, conductivity, somatic cell count, milk yield, and clotting.
4. What is the target? `class1`, where 0 is no mastitis and 1 is mastitis.
5. What is the dataset size? 800 rows.
6. What is the class distribution? 631 negative and 169 positive.
7. Why class weights? To reduce the effect of the minority positive class.
8. What preprocessing exists? StandardScaler is included in candidate pipelines.
9. Is scaling required by Random Forest? Not generally, but the pipeline keeps inference consistent and supports the compared Logistic Regression.
10. What algorithms were compared? Random Forest and Logistic Regression.
11. How is evaluation split? Stratified 80/20 train/test split with random state 42.
12. What CV is used? Stratified 5-fold macro-F1 on the training split.
13. What metrics are calculated? Accuracy, macro F1, ROC-AUC, and classification report.
14. Are exact B values stored? No; only the training script prints them.
15. Why use ROC-AUC? It measures ranking ability across thresholds for the binary output.
16. What is returned? Positive mastitis probability and predicted condition.
17. What does a low probability mean? Low model-confidence risk band, not proof of no disease.
18. Why not merge with Model A? The input domains and targets differ; separate outputs are more interpretable.
19. What if milk data is incomplete? Pydantic requires all six fields when `milk_data` is supplied.
20. What is the main limitation? Dataset-dependent performance and no clinical validation.

# Part 11 - Model C image model

1. What is computer vision? Using image data for classification; here the model predicts one of three cattle-image classes.
2. Why MobileNetV2? It is relatively lightweight and suitable for transfer learning/CPU inference.
3. What is transfer learning? Reusing features learned from ImageNet and training a new task-specific head.
4. What is ImageNet? The pretraining source represented by the torchvision ImageNet weights.
5. What is frozen? `model.features` parameters; only the classifier is trained.
6. What is the head? A linear layer replacing the original classifier output for three classes.
7. Why 224x224? It is the standard input size used by this MobileNetV2 pipeline.
8. Why RGB? PIL converts input images to RGB before transforms.
9. What normalization? Means [0.485, 0.456, 0.406], standard deviations [0.229, 0.224, 0.225].
10. What augmentation? Horizontal flip, rotation, brightness/contrast/saturation changes during training.
11. What is the dataset? 3,244 images from three folders/classes.
12. What is the split? Stratified 70% train, 15% validation, 15% test.
13. Why class weights? The classes have different counts.
14. What is early stopping? Stop after validation macro F1 fails to improve for four epochs.
15. What optimizer? Adam on the classifier parameters.
16. What is the test accuracy? 0.8583 in stored metadata.
17. What is test macro F1? 0.86 in stored metadata.
18. Does it return top-5? It returns ranked predictions for all classes; with three classes, at most three.
19. What happens during inference? Resize/normalize, run softmax, sort class probabilities, apply risk band.
20. What is the risk threshold? 0.70 high, 0.40 moderate, lower low.
21. Does an image prove a disease? No; it is an image-model estimate.
22. What if the image is poor? The model still attempts inference after file validation; field robustness is a limitation.
23. What if the class is unseen? The classifier only knows its three trained classes.
24. How is the model loaded? State dict and metadata are loaded on CPU, then evaluation mode is used.
25. What is the main limitation? Dataset shift, image quality, and lack of clinical validation.

# Part 12 - Model D lumpy skin model

1. Why a separate lumpy model? It focuses on a specific binary visual task instead of the broader three-class task.
2. What are the classes? `Lumpy Skin` and `Normal Skin`.
3. What is the dataset size? 1,024 images, with 324 Lumpy Skin and 700 Normal Skin.
4. What model? MobileNetV2 with a replaced two-class head.
5. What is transfer learning here? ImageNet feature reuse with frozen features and a task-specific classifier.
6. What input size? 224x224 RGB.
7. What split? Stratified 70/15/15 train/validation/test.
8. Why class weights? Lumpy Skin is the minority class.
9. What is early stopping? Four validation-F1 patience epochs.
10. What are the stored results? Accuracy 0.8961, macro F1 0.8775, ROC-AUC 0.9351.
11. What does ROC-AUC represent? Binary ranking performance using the Lumpy Skin probability.
12. Is the result clinically validated? No.
13. Why not use Model C for every lumpy question? Model D is a focused specialist with a different dataset and binary target.
14. Why not combine C and D? They are independent model outputs with different class spaces.
15. What if the image is normal? The specialist can return Normal Skin; it is still only a model estimate.
16. Does D diagnose all cattle diseases? No, only its trained two-class image task.
17. What is the main deployment limitation? Domain shift from curated images to real farmer uploads.
18. How is it selected? Client form sends `model=lumpy`, and backend selects `lumpy_skin_predictor`.
19. Where is its version? `bovicare-lumpy-skin-v1` in metadata.
20. What is the safety message? The API response says a qualified veterinarian should confirm the condition.

# Part 13 - Why four models?

- **Why not one model?** The inputs and tasks differ: binary symptom features, numerical milk features, three-class images, and a lumpy-specific binary image task. Specialization keeps each contract understandable.
- **Why independent?** Each model has its own feature space, label space, artifact, version, and risk output.
- **Why no probability combination?** Probabilities from different models are not necessarily calibrated to the same target or population. The code deliberately preserves separate model groups.
- **Only symptoms:** `/predictions` runs Model A.
- **Only milk:** `/predictions` runs Model B.
- **Both:** `/predictions` runs A and B independently; `combined_risk_level` is the highest individual risk band, not a probability merge.
- **Only image:** `/predictions/image` runs C by default or D when `model=lumpy`.
- **Multiple inputs:** The frontend can call A/B and image inference in sequence; the result page displays separate cards/results.
- **No valid input:** Pydantic rejects no symptoms/milk with 422; frontend rejects no symptom/milk/image before submission.
- **Important distinction:** A case's initial `/cases/triage` value comes from the older preliminary triage service; the main stored Model A/B/C/D rows come from the prediction endpoints.

# Part 14 - Risk classification

1. **What is probability?** A model output between 0 and 1 representing its predicted class score/probability according to that model.
2. **What are thresholds?** >=0.70 high, >=0.40 moderate, otherwise low.
3. **Are thresholds clinical?** No. The code says they are indicative confidence bands requiring validation.
4. **What does high mean?** The model strongly associates the input with a class under this implementation's rule.
5. **What does low mean?** The model's top probability is below 0.40; it does not prove health.
6. **Is risk the same as diagnosis?** No.
7. **How is combined risk produced?** Highest risk level among the separately executed A/B results.
8. **Are C/D risk values merged with A/B?** Not by the ML router; frontend high-risk display also observes available result cards.
9. **Why use a band?** It is easier for a farmer/doctor to scan than a raw number alone.
10. **What is calibration?** Whether predicted probabilities match observed frequencies; calibration is not established here.
11. **Can a high probability be wrong?** Yes, especially with distribution shift or incorrect input.
12. **Can a low probability hide disease?** Yes; absence of model confidence is not absence of disease.
13. **What does a high-risk notification mean?** A high model-confidence risk event was logged for doctor review.
14. **What should the farmer do?** Seek qualified veterinary assessment, especially for high-risk results.
15. **What should you claim in viva?** Say “indicative model-confidence risk,” never “clinically validated severity.”

# Part 15 - Image processing and storage

1. Supported MIME types: JPEG, PNG, WEBP, BMP.
2. Maximum configured size: 10 MB.
3. Validation steps: MIME check, bounded read, size check, Pillow open/verify.
4. Preprocessing for C/D: RGB conversion, resize 224x224, tensor conversion, ImageNet normalization.
5. Storage: UUID-generated filename under configured private upload directory.
6. Database: stores filename/content type and links to case/cattle/owner; bytes are outside the DB.
7. Access: authenticated `/cases/{id}/image`, with farmer ownership check and doctor access.
8. Replacement: current case image is replaced and old file removed when a new linked image is stored.
9. Traversal: generated names and resolved-root check stop `../` path use.
10. Invalid file: 415.
11. Oversized file: 413.
12. Missing file: 404.
13. Unauthenticated image: 401.
14. Poor quality: no quality score or rejection beyond file validity; this is a limitation.
15. Future hardening: malware scanning, object storage, retention policy, and content-security controls are future scope.

# Part 16 - Veterinary workflow

1. A doctor logs in and is routed to `/veterinary`.
2. The dashboard lists cases, filters by search/risk/status, and links to case details.
3. Case details load persisted model groups, private image, notifications, observations, and review fields.
4. The doctor adds required notes and sends `PUT /cases/{id}/review` with `veterinarian_notes` and `review_status`.
5. Status is `pending_review` initially; accepted values are pending, pending_review, and reviewed, with pending normalized to pending_review.
6. High-risk events target the doctor role and appear in case details.
7. The doctor can download the PDF report.
8. This is human-in-the-loop: AI provides evidence, doctor applies clinical judgment.
9. **Not implemented:** the visible confirm-diagnosis and treatment/advice fields are not persisted by the current request.
10. **Not implemented:** automated treatment recommendations are not generated.

# Part 17 - PDF report

1. **Why PDF?** A portable case record for review or sharing.
2. **Library:** ReportLab.
3. **Endpoint:** `GET /api/v1/cases/{case_id}/report`.
4. **Auth:** authenticated owner or doctor according to case access rules.
5. **Includes:** case ID, cattle details, farmer information, symptoms, temperature, review status, veterinarian notes, notification statuses, and model sections.
6. **Model sections:** Model A, B, C, and D are listed separately; unavailable models are marked unavailable.
7. **Probabilities:** Persisted rows are shown as percentages.
8. **Disclaimer:** AI output is decision support and requires qualified veterinarian confirmation.
9. **Download:** frontend requests a blob and triggers a named PDF download.
10. **Verification:** final verification confirmed a PDF and required Model A-D, review note, notification, and disclaimer text.

# Part 18 - Notification system

1. **When generated?** When a case is high risk during triage or a linked prediction produces high risk.
2. **Which models?** General triage, Model A, Model B, Model C, or Model D can supply the event depending on the calling path.
3. **What is high risk?** The implementation's top-probability band at or above 0.70, or preliminary urgent triage high.
4. **Duplicate prevention?** Existing same-case, `high_risk_case`, and same model payload is reused.
5. **Where stored?** `notification_logs` with status, target role, event payload, and timestamp.
6. **Default development status?** `mock` when `notification_provider` is `mock`.
7. **Other status behavior?** Non-mock with no credentials becomes `queued`; with credentials it currently becomes `failed` because no delivery client is implemented.
8. **Is SMS/email delivered?** No. Do not claim real delivery.
9. **Who is targeted?** Role string `doctor`.
10. **Future integration:** implement provider adapters, retry policy, secrets management, delivery callbacks, and audit handling.

# Part 19 - Testing

## What is actually present

- `verify_phase3.py`: auth, role checks, triage, case access, review authorization.
- `verify_phase4.py`: cattle CRUD, ownership, case-cattle linking, regressions.
- `verify_phase5.py`: prediction routing A/B, no-input validation, ownership, regression.
- `verify_phase6.py`: image MIME/auth/model behavior and regression.
- `verify_phase7.py`: persistence, case prediction grouping, model separation, notes, access.
- `verify_phase8.py`: review, all four model groups, report content, access.
- `verify_phase9.py`: private image security, size/type/path checks, notifications.
- `verify_final.py`: end-to-end authentication, ownership, all four models, image, review, PDF.

The scripts are executable integration/verification scripts rather than a pytest suite. They dynamically print their own phase counts. The current run of `verify_final.py` passed **26/26 tests**. The current frontend `npm run build` also passed. Do not claim unit-test counts that are not present.

## Testing questions

1. **Are these unit tests?** Mostly API integration/verification scripts using urllib and test data.
2. **What does 26/26 mean?** All checks in `verify_final.py` passed in that run, not that every possible behavior is proven.
3. **What was tested?** Authentication, cross-owner blocking, case/cattle creation, A/B prediction, C/D image prediction, private image retrieval, doctor review, and PDF content.
4. **Were image errors tested?** Phase 9 tests unsupported type, oversize, missing case/image, and path traversal.
5. **Were notifications tested?** High-risk creation, mock status, doctor target, no normal-case event, and duplicate-related behavior are covered across scripts.
6. **Was frontend behavior browser-tested?** The repository's supplied scripts do not constitute browser automation; the production build passed.
7. **Were Model A/B metrics rerun?** Not as part of final verification; their scripts contain evaluation code but no stored metric metadata.
8. **What is a remaining test gap?** More unit tests, browser tests, negative model tests, load tests, calibration tests, and clinical validation.
9. **Why regression scripts?** Later phases recheck earlier authentication, cattle, and review behavior after adding ML/image/report features.
10. **What should be said honestly?** “The integration verification passed; broader statistical and clinical validation remains future work.”

# Part 20 - Limitations

- **LIMITATION:** Model A's held-out test is only 26 rows, one per class as described by its training script.
- **LIMITATION:** Model A/B exact final metrics are not stored in repository metadata.
- **LIMITATION:** Image metrics come from their dataset splits, not field deployment.
- **LIMITATION:** Datasets may not represent all breeds, environments, cameras, disease stages, or co-morbidities.
- **LIMITATION:** Unknown symptoms are ignored by Model A rather than explicitly rejected.
- **LIMITATION:** Model classes cannot reliably represent diseases outside training labels.
- **LIMITATION:** Risk thresholds are model-confidence bands, not clinically validated thresholds.
- **LIMITATION:** No calibration or prospective clinical study is included.
- **LIMITATION:** Real email/SMS delivery is not implemented.
- **LIMITATION:** Local filesystem image storage and SQLite are development-friendly choices.
- **LIMITATION:** Doctor treatment/advice UI is not persisted.
- **LIMITATION:** No IoT sensor integration exists.
- **LIMITATION:** No rate limiting or production deployment hardening is shown.
- **LIMITATION:** The preliminary triage compatibility service and trained Model A are separate code paths, which should be explained clearly.

## Strong answer

"The main limitations are dataset dependence and the lack of clinical validation. Model A also has a very small 26-row held-out test set, so its metric would not be strong evidence of generalization. The image models can be affected by image quality and field conditions. The risk thresholds are transparent engineering thresholds, not veterinary thresholds. Notifications are currently logged/mock rather than delivered through a real provider. Therefore I present BoviCare as decision support and require veterinarian confirmation."

# Part 21 - Future scope

1. IoT sensors for temperature, milk, activity, and rumination: **future**.
2. Real-time cattle monitoring: **future**.
3. More diseases and larger representative clinical datasets: **future**.
4. Better image models and field-data validation: **future**.
5. Multilingual farmer interface: **future**.
6. Native mobile application: **future**.
7. Real SMS/email provider adapters: **future**.
8. Clinically validated treatment support: **future and requires governance**.
9. Cloud deployment and object storage: **future**.
10. Monitoring, drift detection, calibration, and model retraining: **future**.
11. Browser automation and stronger automated test suite: **future improvement**.
12. Persisted diagnosis/treatment fields: **future**.

# Part 22 - Technical cross-questions

1. FastAPI? Python API framework with validation and OpenAPI.
2. React? Component-based UI library.
3. Vite? Frontend dev server/build tool.
4. REST? Resource-oriented HTTP interface.
5. Axios? JavaScript HTTP client.
6. JWT? Signed bearer token.
7. SQLAlchemy? Python ORM/database toolkit.
8. SQLite? Embedded file database.
9. PostgreSQL? Server relational database option.
10. Random Forest? Ensemble of decision trees.
11. Transfer learning? Reusing a pretrained model for a new task.
12. MobileNetV2? Lightweight CNN architecture.
13. CNN? Neural network suited to spatial image patterns.
14. Classification? Assigning an input to class labels.
15. Multi-class? More than two possible classes.
16. Binary? Two possible classes.
17. Accuracy? Correct predictions divided by all predictions.
18. Precision? Of predicted positives, the fraction truly positive.
19. Recall? Of actual positives, the fraction found.
20. F1? Harmonic mean of precision and recall.
21. Macro F1? Average F1 giving each class equal weight.
22. ROC-AUC? Area under threshold-ranking curve for binary classification.
23. Overfitting? Learning training-specific patterns that fail to generalize.
24. Underfitting? Model too simple to learn useful patterns.
25. Cross-validation? Repeated train/validation folds for model comparison.
26. Class imbalance? Unequal class frequencies.
27. Class weights? Higher loss importance for selected classes.
28. Early stopping? Stop when validation metric stops improving.
29. ImageNet? Dataset/source of pretrained image weights here.
30. Preprocessing? Converting raw input to model-ready representation.
31. Feature extraction? Converting data into model input signals.
32. API? Program interface exposed to another program.
33. HTTP 401? Authentication required/invalid.
34. HTTP 403? Authenticated but forbidden.
35. HTTP 404? Resource not found.
36. HTTP 422? Validation/unprocessable input.
37. HTTP 201? Created successfully.
38. Primary key? Unique table row identifier.
39. Foreign key? Reference to another table.
40. CORS? Browser cross-origin policy control.
41. Hashing? One-way representation used for password storage.
42. Authentication vs authorization? Identity versus permission.
43. Why SQLite? Easy local setup.
44. Why PostgreSQL? Better server-scale relational deployment option.
45. Why macro F1? Equal class importance.
46. Why class weights? Address unequal class counts.
47. Why 224x224? MobileNetV2 pipeline input convention.
48. Why separate models? Different inputs and targets.
49. What is softmax? Converts logits to values summing approximately to one.
50. What is model version? Identifier stored with predictions/artifacts for traceability.

# Part 23 - Examiner trick questions

1. **High Model A accuracy means clinical accuracy?** No; its test set is very small and dataset-specific, and clinical validation is absent.
2. **Why is Model A test set small?** The supplied Testing.csv has 26 rows, one per class according to the training script.
3. **Why trust prediction?** Treat it as an assistive estimate; trust is supported by transparent model/version/probability storage, not by claiming certainty.
4. **Can AI replace a vet?** No.
5. **Why independent models?** Different input spaces and target definitions.
6. **Why not merge probabilities?** They are not guaranteed to be calibrated to the same event.
7. **Why not one deep model?** That would require a shared multimodal dataset and a defined joint target; the current project has separate datasets/tasks.
8. **Poor image?** File validity passes, but prediction quality may degrade; no quality classifier exists.
9. **Wrong symptoms?** Model A encodes what is submitted; incorrect input can produce an unreliable result.
10. **Unseen disease?** It cannot be reliably recognized outside trained classes.
11. **Farmer accesses another case?** 403.
12. **Farmer calls doctor review?** 403.
13. **Doctor modifies cattle?** 403 because cattle writes are farmer-only.
14. **Unauthenticated prediction?** 401.
15. **Why FastAPI?** Typed validation, dependency injection, OpenAPI, and async uploads.
16. **Why React?** Componentized interactive SPA and client routing.
17. **Why MobileNetV2?** Lightweight transfer-learning model suitable for the dataset and CPU inference.
18. **Why Random Forest?** Good fit for tabular/binary features and native probabilities.
19. **Biggest limitation?** No clinical validation and dataset/generalization limitations.
20. **Three more months?** Collect clinical data, calibrate/validate models, add browser tests and provider adapters.
21. **How deploy?** Use PostgreSQL, secure environment secrets, object storage, HTTPS, backend/frontend hosting, logging, and monitoring; this is deployment scope, not current local setup.
22. **Scale to thousands?** Stateless API workers, PostgreSQL, object storage, queues for inference/notifications, caching, and observability.
23. **Does combined risk combine probabilities?** No; it takes the highest risk label only for A/B.
24. **Does triage equal Model A?** Not exactly. `/cases/triage` uses the older preliminary triage service; `/predictions` uses active trained Model A.
25. **Are C/D always run?** No; only `/predictions/image` runs them when an image is uploaded.
26. **Are notifications delivered?** No; current default is mock logging.
27. **Are treatment notes saved?** Veterinarian notes are saved; treatment/advice field is currently not sent/persisted.
28. **Does Recharts power a dashboard?** No current source uses it.
29. **Can a doctor self-register in production?** The backend rejects doctor registration outside development/test.
30. **What did final verification prove?** 26/26 end-to-end checks passed in the current run, not clinical effectiveness.

# Part 24 - Personal contribution

The repository alone cannot prove individual ownership. Do not claim that you personally wrote every file unless that is true and you can explain it.

## 30-second answer

"My technical contribution can be described from the implemented project areas I worked on: integrating the React frontend with the FastAPI backend, connecting authenticated case workflows to the prediction services, persisting separate model results, and supporting image, notification, review, and PDF flows. I can explain the routers, schemas, SQLAlchemy models, model routing, ownership checks, and verification scripts. I would separate that from team contributions rather than claiming unsupported individual work."

## 1-minute answer

"My contribution was focused on turning the cattle diagnosis idea into an end-to-end application. I worked with the React pages and Axios API integration, the FastAPI routers and Pydantic contracts, SQLAlchemy persistence, JWT role checks and ownership validation, and the ML service integration. The important technical decision was to keep the four models independent and store their results with model names, versions, ranks, probabilities, and risk levels. I also worked with private image validation/storage, high-risk event logging, ReportLab reports, veterinarian review, and the phase verification scripts. I would be honest about the exact division of work with my team and would not claim undocumented features."

# Part 25 - Complete mock viva

## Round 1 - 10 easy questions

1. **What is your title?** BoviCare AI: Intelligent Cattle Diagnosis Platform. **Follow-up:** Main purpose? **Answer:** Preliminary AI-assisted cattle health assessment and veterinary review.
2. **Who uses it?** Farmers and doctors. **Follow-up:** Roles? **Answer:** `farmer` and `doctor`.
3. **Frontend?** React/Vite. **Follow-up:** API client? **Answer:** Axios.
4. **Backend?** FastAPI/Uvicorn. **Follow-up:** Docs? **Answer:** OpenAPI/Swagger through FastAPI.
5. **Database?** SQLite locally, PostgreSQL-ready. **Follow-up:** ORM? **Answer:** SQLAlchemy.
6. **What does farmer do?** Manage cattle and submit cases. **Follow-up:** Can farmer review? **Answer:** No, doctor-only.
7. **What does doctor do?** Review cases and add notes/status. **Follow-up:** Can doctor create cattle? **Answer:** No.
8. **How many models?** Four independent models. **Follow-up:** Why? **Answer:** Different inputs/tasks.
9. **Can it replace a vet?** No. **Follow-up:** Why? **Answer:** No clinical validation; decision support only.
10. **Report format?** PDF. **Follow-up:** Library? **Answer:** ReportLab.

## Round 2 - 15 project questions

1. **Complete workflow?** Auth -> cattle/case -> prediction -> persistence -> review/report. **Follow-up:** Storage? **Answer:** DB plus private filesystem images.
2. **Why REST?** Separate clients and resource contracts. **Follow-up:** Example? **Answer:** `POST /api/v1/predictions`.
3. **What is triage?** Farmer-only case creation with preliminary assessment. **Follow-up:** Is it Model A? **Answer:** The endpoint uses the compatibility triage service; active Model A runs through predictions.
4. **Why separate frontend?** Independent UI/backend concerns. **Follow-up:** Future client? **Answer:** Mobile can call same API.
5. **How is case history available?** `/cases` and case prediction endpoints. **Follow-up:** Access? **Answer:** Owner/doctor rules.
6. **What is high risk?** Indicative top-probability band >= .70 or urgent preliminary triage. **Follow-up:** Clinical? **Answer:** No.
7. **What is remote review?** Doctor accesses persisted case and adds notes/status. **Follow-up:** Treatment? **Answer:** Not automatically implemented.
8. **Why reports?** Portable summary. **Follow-up:** Data? **Answer:** Case, predictions, review, notifications, disclaimer.
9. **Why image private?** Health-related case data. **Follow-up:** Mechanism? **Answer:** Authenticated endpoint and path checks.
10. **What if no input?** 422. **Follow-up:** Why? **Answer:** Pydantic model validator.
11. **What if duplicate email?** 409. **Follow-up:** Where? **Answer:** Register route checks email.
12. **What is CORS?** Browser origin control. **Follow-up:** Does it replace auth? **Answer:** No.
13. **What is model version?** Traceability identifier. **Follow-up:** Stored? **Answer:** Each prediction row.
14. **What is notification status?** Current event state such as mock. **Follow-up:** Delivery? **Answer:** No real provider client.
15. **What passed?** Final 26/26; frontend build passed. **Follow-up:** Clinical validation? **Answer:** Not performed.

## Round 3 - 15 ML questions

1. **Model A input?** Binary symptoms. **Follow-up:** Output? **Answer:** Up to five ranked diseases.
2. **Model B input?** Six milk measurements. **Follow-up:** Output? **Answer:** Mastitis/No Mastitis.
3. **Model C classes?** HEALTHY, LSD, RINGWORM, FMD, IBK, PEDICULOSIS, DERMATOPHILOSIS. **Follow-up:** Architecture? **Answer:** EfficientNet-B0.
4. **Model D classes?** Lumpy Skin, Normal Skin. **Follow-up:** Metric? **Answer:** Accuracy .8961, macro F1 .8775, ROC-AUC .9351.
5. **Why four?** Specialization. **Follow-up:** Merge? **Answer:** No probability merge.
6. **Why RF?** Tabular/binary suitability and probabilities. **Follow-up:** Selection? **Answer:** 5-fold macro-F1 comparison.
7. **Why MobileNet?** Lightweight transfer learning. **Follow-up:** Frozen? **Answer:** Feature layers.
8. **What is 224?** Image input size. **Follow-up:** RGB? **Answer:** PIL converts to RGB.
9. **What is macro F1?** Equal-class average F1. **Follow-up:** Why? **Answer:** Handles class imbalance fairly.
10. **What is ROC-AUC?** Binary ranking metric. **Follow-up:** Which stored? **Answer:** Model D metadata.
11. **What is early stopping?** Stop after validation F1 stalls. **Follow-up:** Patience? **Answer:** Four.
12. **What are class weights?** Loss weighting for imbalance. **Follow-up:** Models? **Answer:** Image models and Model B RF candidate.
13. **Can unseen disease be found?** No reliable claim. **Follow-up:** Why? **Answer:** Closed training label space.
14. **Are A/B exact scores known?** Not stored. **Follow-up:** Source? **Answer:** Training scripts calculate them.
15. **Clinical accuracy?** Cannot claim. **Follow-up:** Reason? **Answer:** Dataset/test/validation limitations.

## Round 4 - 15 backend/database questions

1. What is a router? Grouped API module. **Follow-up:** Examples? Auth/cases/cattle/predictions.
2. What is a schema? Pydantic contract. **Follow-up:** Example? `PredictionRequest`.
3. What is a model? SQLAlchemy table mapping. **Follow-up:** Example? `ClinicalCase`.
4. What is dependency injection? FastAPI supplies DB/current user. **Follow-up:** Syntax? `Depends`.
5. What does POST predictions do? Route/store A/B. **Follow-up:** Auth? Required.
6. What does image endpoint do? Validate/run/store image/result. **Follow-up:** MIME? Four types.
7. What does 403 mean? Forbidden. **Follow-up:** Example? Cross-farmer case.
8. What is primary key? Row ID. **Follow-up:** All tables? Integer IDs.
9. What is foreign key? Cross-table reference. **Follow-up:** Cattle owner? `farmer_id`.
10. Why SQLite? Local simplicity. **Follow-up:** Production option? PostgreSQL.
11. Where are images? Filesystem. **Follow-up:** DB? Metadata only.
12. How report? ReportLab stream. **Follow-up:** Auth? Case access.
13. How review? Doctor PUT. **Follow-up:** Fields? Notes/status.
14. How notification? High-risk service/log. **Follow-up:** Provider? Mock logic only.
15. What did verification cover? API/integration flow. **Follow-up:** Count? Final 26/26.

## Round 5 - 10 security questions

1. How password stored? Argon2 hash. **Follow-up:** Plaintext? Never.
2. What is JWT? Signed bearer token. **Follow-up:** Expiry? Yes.
3. Who enforces role? Backend dependency. **Follow-up:** Frontend? UX only.
4. Cross-farmer access? 403. **Follow-up:** Where? Ownership helper.
5. Unauthenticated access? 401. **Follow-up:** Header? Bearer.
6. Image traversal? Root resolution. **Follow-up:** Filename? UUID.
7. CORS? Origin control. **Follow-up:** Auth? Separate.
8. Secret key? Environment configuration. **Follow-up:** Production default? Rejected.
9. Doctor registration? Development/test only. **Follow-up:** Production? Admin provisioning required.
10. Production gaps? Rate limiting, provider hardening, deployment/security controls. **Follow-up:** Status? Future scope.

## Round 6 - 10 difficult/trick questions

1. **Do four probabilities form one diagnosis?** No, they remain independent.
2. **Why does combined risk exist?** Convenience label using highest risk, not probability fusion.
3. **Is Model A test result reliable?** It is a small dataset test result, not clinical evidence.
4. **What if symptom is unknown?** It is ignored by the feature-vector builder.
5. **What if image is valid but irrelevant?** The model may still return a class; quality/relevance detection is not implemented.
6. **Is notification an email?** No, a logged event with mock/queued/failed status logic.
7. **Are treatment text fields saved?** Current review request saves notes/status only.
8. **Does Recharts show analytics?** No current source uses it.
9. **Can doctor modify a farmer's cattle?** No, doctor has read access to cattle list but cattle writes are farmer-only.
10. **What would you improve first?** Clinical dataset/validation and calibrated outputs, then operational hardening.

# Part 26 - Last-minute revision sheet

**Project:** BoviCare AI: Intelligent Cattle Diagnosis Platform  
**Purpose:** AI-assisted preliminary cattle health assessment and veterinary review  
**Users:** Farmer and veterinary doctor  
**Frontend:** React, Vite, React Router, Tailwind CSS, Axios, Lucide React; Recharts dependency unused  
**Backend:** Python, FastAPI, Uvicorn  
**Database:** SQLAlchemy; SQLite default; PostgreSQL-ready  
**Authentication:** JWT bearer tokens, Argon2 via pwdlib, role and ownership checks  
**ML Models:** Four independent models  
**Model A:** Random Forest, 93 binary symptoms, 26 classes, top-5 output  
**Model B:** Mastitis specialist, six milk features, binary output  
**Model C:** EfficientNet-B0, seven image classes; 224x224 RGB with ImageNet normalization
**Model D:** MobileNetV2, Lumpy/Normal, accuracy .8961, macro F1 .8775, ROC-AUC .9351  
**Image model:** 224x224 RGB, ImageNet normalization, private upload, max 10 MB  
**Main APIs:** auth, cattle, cases, predictions, image, report, notifications, review, health  
**Risk:** .70 high, .40 moderate, otherwise low; indicative model confidence only  
**Reports:** ReportLab PDF with case, model, review, notification, disclaimer data  
**Notifications:** High-risk database event; default mock, no real email/SMS client  
**Testing:** Verification scripts; final 26/26 passed; frontend build passed  
**Limitations:** Dataset shift, no clinical validation, Model A small test set, non-clinical thresholds, provider dependency  
**Future scope:** IoT, more data/diseases, mobile/multilingual, real providers, deployment, monitoring/retraining

## 50 questions I must know before viva

1. What is BoviCare? AI-assisted cattle decision-support platform.
2. Who are users? Farmers and veterinary doctors.
3. What is the frontend? React/Vite SPA.
4. What is the backend? FastAPI served by Uvicorn.
5. What is the database? SQLite default, PostgreSQL-ready.
6. What is ORM? SQLAlchemy.
7. How authenticate? JWT bearer token.
8. How hash passwords? Argon2 through pwdlib.
9. What are roles? Farmer and doctor.
10. What is authorization? Role plus ownership checking.
11. What is Model A? General symptom classifier.
12. Model A algorithm? Random Forest selected by CV.
13. Model A features? 93 binary symptom features.
14. Model A output? Up to five ranked diseases.
15. Model A test size? 26 rows.
16. Are A metrics stored? No exact values in metadata.
17. What is Model B? Mastitis milk-parameter classifier.
18. Model B features? Six named milk fields.
19. Model B output? Mastitis/No Mastitis and probability.
20. What is Model C? Seven-class cattle image classifier.
21. Model C architecture? EfficientNet-B0, PyTorch.
22. Model C classes? HEALTHY, LSD, RINGWORM, FMD, IBK, PEDICULOSIS, DERMATOPHILOSIS.
23. What is the Model C input? 224x224 RGB with ImageNet normalization.
24. Does Model C use the old three-class MobileNetV2 artifact? No; the old artifact remains as a backup, while inference uses the final EfficientNet checkpoint.
25. What is Model D? Lumpy Skin binary image specialist.
26. Model D accuracy? 0.8961.
27. Model D macro F1? 0.8775.
28. Model D ROC-AUC? 0.9351.
29. Why separate models? Different inputs/tasks.
30. Are probabilities merged? Never.
31. What does combined risk mean? Highest separate A/B risk band.
32. What are risk thresholds? .70 high, .40 moderate.
33. Are thresholds clinical? No.
34. What happens with symptoms only? Model A.
35. Milk only? Model B.
36. Both? A and B independently.
37. Image endpoint models? C or D by form selection.
38. Supported image types? JPEG, PNG, WEBP, BMP.
39. Image maximum? 10 MB.
40. Where are image bytes? Private filesystem.
41. What is a case? Persisted clinical submission.
42. What is prediction storage? Separate model/rank rows.
43. What does doctor review save? Notes and status.
44. Are treatment inputs saved? No, current UI fields are not sent.
45. What is a notification? High-risk database event.
46. Are email/SMS real? No.
47. What is the PDF library? ReportLab.
48. What did final verification show? 26/26 passed.
49. Can AI replace a vet? No.
50. Biggest limitation? No clinical validation and dataset-dependent generalization.

# Study order

Study this document in this order: **Last-minute revision sheet -> 2-minute introduction -> Part 13 (four-model routing) -> Parts 8-12 (ML) -> Parts 5-7 (backend/database/security) -> Parts 19-23 (testing, limitations, trick questions).**

The exact preparation file created for this repository is:

- [docs/viva_preparation_guide.md](viva_preparation_guide.md)

No project source code was modified for this preparation task.
