# FINDORA
### AI-Powered Lost & Found Platform for Meerut Institute of Engineering and Technology

**Find it. Match it. Return it.**

FINDORA is a campus-focused Lost & Found platform designed for **Meerut Institute of Engineering and Technology (MIET)**. It helps students and administrators report, discover, match, verify and recover lost belongings through an intelligent matching system and a secure communication workflow.

Instead of relying on scattered WhatsApp groups, notice boards and manual registers, FINDORA brings the entire lost-and-found process into one organized platform.

---

## ✨ Key Features

FINDORA provides two separate interfaces within a single Flask application.

### 👤 1. User Interface

Available at `/`

| Feature | Description |
|---|---|
| **Home & Search** | Browse and search lost and found items using categories, stickers and photos. |
| **Report Lost / Found** | Submit item reports with descriptions, photos, dates and locations. |
| **Automatic Location Detection** | Detect and save the reported item's location when permission is granted. |
| **High-Risk Suggestions** | Display written suggestions for potentially high-risk situations. |
| **Location Trail** | Optional location tracking for up to 6 hours, subject to user permission. |
| **AI-Powered Matching** | Automatically discover potentially matching lost and found reports. |
| **Anonymous Chat** | Communicate with the other party through anonymized conversations on AI matches. |
| **Personal Dashboard** | View personal reports, claims, claims on submitted reports and AI matches. |
| **Past Locations Map** | Review previously recorded location information on a map. |
| **Anonymized Claim Chat** | Communicate during the ownership verification process without exposing personal contact details. |
| **Contact Admin** | Directly report problems, submit questions and contact administrators. |
| **Notifications & Alerts** | Receive updates about matches, claims and platform activity. |

### 🛡️ 2. Admin Console

Available at `/admin`

The administrator interface provides centralized control over platform activity through a sidebar-based dashboard.

| Module | Description |
|---|---|
| **Dashboard** | Overview of platform activity and important statistics. |
| **All Reports** | View reported items, photographs, reporters and stored GPS coordinates. |
| **AI Match Scores** | Compare AI similarity scores against the configured matching threshold. |
| **Claims Management** | Review ownership claims and make final approval or rejection decisions. |
| **AI Match Log** | Inspect every scored report pair, including matches rejected by the threshold. |
| **User Messages** | Reply to users or initiate conversations with any user. |
| **User Management** | View and manage registered platform users. |
| **Categories** | Manage item categories. |
| **Locations** | Manage campus locations and location records. |
| **Organizations** | Manage organization-level records. |
| **Flags** | Review flagged content and platform activity. |
| **Audit Log** | Maintain a record of important administrative actions. |

---

## 🧠 AI Matching Engine

FINDORA uses a locally executed, explainable similarity-based matching engine. **No external AI API is required.**

When a new report is submitted, the matching service compares it with eligible open reports of the opposite type.

### Matching workflow

1. A user submits a lost or found item report.
2. The matching engine retrieves eligible opposite-type reports.
3. Six similarity signals are calculated.
4. The signals are combined into a weighted score.
5. The score is compared with the configured matching threshold.
6. Qualifying matches are saved and users are notified.
7. Every scored pair, including rejected pairs, is recorded in the AI match log.

### Six matching signals

| Signal | Weight | Technique |
|---|---:|---|
| Description, title and features | 30% | TF-IDF and cosine similarity |
| Category | 15% | Exact category matching |
| Location | 15% | Location matching and name similarity |
| Colour, brand and model | 15% | String similarity using `difflib` |
| Photograph | 15% | Perceptual difference hashing (dHash) |
| Date | 10% | Time-based linear similarity decay |
| **Total** | **100%** | **Weighted similarity score** |

### Technical details

- **Text similarity:** TF-IDF using one-word and two-word terms, followed by cosine similarity.
- **Category matching:** Exact category comparison.
- **Location matching:** Exact location comparison or name similarity.
- **Attribute matching:** String similarity for colour, brand and model.
- **Image matching:** Pillow-based perceptual difference hashing (dHash), with Hamming distance.
- **Date matching:** Similarity decreases linearly over a 14-day period.

If a report does not contain a particular signal, its weight is excluded and the remaining weights are normalized.

### Matching configuration

| Setting | Default |
|---|---|
| Matching threshold | 80% |
| Candidate report window | ±30 days |
| Maximum candidates | 200 |
| Candidate type | Opposite report type |
| Organization scope | Same organization |

The matching threshold can be configured through the `MATCH_THRESHOLD` environment variable.

**Important:** The matching score represents similarity, not a calibrated probability that two reports refer to the same physical object. AI matching suggests possible connections; it does not make final ownership decisions.

### Claim verification

FINDORA also assists administrators during ownership verification.

- Claimant answers are compared with the owner's encrypted private verification details.
- TF-IDF and sequence similarity are combined to calculate verification confidence.
- Administrators review the available evidence and make the final decision.
- Claims are never automatically approved by the AI engine.

---

## 🔐 Privacy and Security

FINDORA is designed to protect users while enabling safe communication and item recovery.

- **Password protection:** Passwords are stored as salted hashes.
- **Encrypted private proofs:** Sensitive ownership verification information is Fernet-encrypted.
- **Controlled access:** Private verification details are restricted to authorized administrators.
- **Anonymous communication:** Users communicate through role-based identities such as Reporter and Claimant.
- **Contact masking:** Phone numbers, email addresses and social handles are masked in supported communication workflows.
- **CSRF protection:** Forms use CSRF protection against cross-site request forgery.
- **Rate limiting:** Login and other protected routes use rate-limiting controls.
- **Image validation:** Uploaded images undergo file validation.
- **Role-based authorization:** Protected functionality is restricted according to user roles.
- **Audit logging:** Important administrative activities are recorded.
- **Location privacy:** Location-related functionality depends on user permission.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript, Jinja2 |
| Database | SQLite |
| ORM | Flask-SQLAlchemy |
| Authentication | Flask-Login |
| Forms & Validation | Flask-WTF, WTForms |
| AI Text Matching | TF-IDF, cosine similarity |
| Image Processing | Pillow, perceptual hashing |
| Similarity Algorithms | Python `difflib` |
| Encryption | Fernet |
| Testing | Pytest |
| Environment Configuration | python-dotenv |

### AI dependency

The core matching engine includes a built-in TF-IDF implementation. Scikit-learn can optionally be installed for the alternative implementation.

No external AI API key or paid AI service is required for the core matching functionality.

---

## 📁 Project Structure

```text
FINDORA/
│
├── app/
│   ├── auth/
│   ├── main/
│   ├── items/
│   ├── matching/
│   ├── claims/
│   ├── messaging/
│   ├── support/
│   ├── notifications/
│   ├── admin/
│   ├── models/
│   ├── utils/
│   ├── templates/
│   └── static/
│       ├── css/
│       ├── js/
│       ├── img/
│       ├── stickers/
│       └── sample/
│
├── tests/
│
├── docs/
│   ├── TESTING_STEPS.md
│   ├── DATABASE_SIMPLE.md
│   └── AI_API_OPTION.md
│
├── instance/
├── uploads/
│
├── run.py
├── seed.py
├── sample_data.py
├── requirements.txt
├── requirements-optional.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.11 or a compatible Python version supported by the project's dependencies.
- pip package manager.
- Git (optional, for cloning the repository).

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd FINDORA
```

Alternatively, download and extract the project ZIP.

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows:**

```bash
venv\Scripts\activate
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a reference.

```env
SECRET_KEY=your-long-random-secret-key
DATABASE_URL=sqlite:///findora.db
MAX_CONTENT_LENGTH=16777216
MATCH_THRESHOLD=0.80
```

Generate a secure secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `SECRET_KEY`.

**Security note:** Never commit your actual `.env` file, secret key or private credentials to GitHub. Keep the secret key stable when encrypted verification data already exists.

### 6. Initialize the sample database

```bash
python seed.py
```

This creates or rebuilds the local database and loads demonstration data.

**Warning:** Running `seed.py` rebuilds the database and can delete existing records. Use it only when you are comfortable resetting the local database.

### 7. Start the application

```bash
python run.py
```

Open the application in your browser:

**http://127.0.0.1:5000**

---

## 🔑 Demo Login Credentials

The sample database provides the following demonstration accounts.

| Role | Email | Password |
|---|---|---|
| Student | `user1@findora-demo.com` | `Demo1234` |
| Student | `user2@findora-demo.com` | `Demo1234` |
| Student | `user3@findora-demo.com` | `Demo1234` |
| Student | `user4@findora-demo.com` | `Demo1234` |
| Student | `user5@findora-demo.com` | `Demo1234` |
| Administrator | `admin@findora-demo.com` | `Admin1234` |

These are demonstration credentials. Change or disable them before deploying a public production instance.

You do not need to register to test the sample accounts.

---

## 🧪 Testing

FINDORA includes a Pytest suite for checking important application functionality.

Run the complete test suite:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest -v tests/test_advanced.py
```

### Manual testing

Automated tests should be followed by browser-based testing of both interfaces.

Refer to:

- `docs/TESTING_STEPS.md` — step-by-step testing instructions.
- `docs/DATABASE_SIMPLE.md` — plain-language explanation of the database.
- `docs/AI_API_OPTION.md` — information about the current AI implementation and optional API integration.

Recommended manual checks include:

- Student and administrator login.
- Lost and found report submission.
- Photo upload and display orientation.
- AI matching and match notifications.
- Claim submission and administrator review.
- Anonymous messaging.
- Location detection and location history.
- Support requests and notifications.
- Administrative management and audit logs.

---

## 🗺️ Campus Location Configuration

FINDORA is designed around the MIET campus environment.

The coordinates included in `sample_data.py` are approximate demonstration values. Administrators should update the location records through **Admin → Locations** to reflect accurate campus locations.

Location detection and optional location trails depend on browser permissions and device support.

---

## 🔧 Troubleshooting

### Login does not work

- Run `python seed.py` to load the demonstration accounts into a fresh local database.
- Use the exact demonstration email and password.
- Check that the virtual environment is active.
- Check the terminal for application errors.

The login form supports the demonstration accounts included in the sample database. Older `.local` demo accounts may also remain compatible with the current version.

### Dependency installation errors

If dependency installation attempts to compile packages or fails on a newer Python version, try Python 3.12:

```bash
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Use a compatible Python version and the project's pinned dependency requirements if installation issues continue.

### Database errors

For a fresh demonstration setup:

```bash
python seed.py
```

For an existing database, avoid deleting it or running the seed script until its records have been backed up.

The application also includes local SQLite schema initialization and migration support for missing tables and columns.

### Image upload problems

- Check that the uploaded file is a supported image.
- Check that the file size is within the configured upload limit.
- Check that the `uploads/` directory is available and writable.
- Check the application terminal for image-processing errors.

### Optional Scikit-learn installation

The core matching engine works without Scikit-learn.

To install the optional dependency:

```bash
pip install -r requirements-optional.txt
```

The optional implementation uses the same intended text-similarity approach.

---

## 🚀 Future Scope

Potential future improvements include:

- Advanced semantic text matching.
- OCR-based item identification.
- Email and SMS notifications.
- Mobile application integration.
- Real-time messaging.
- Multi-campus item discovery.
- Enhanced analytics and recovery insights.

These are extension possibilities and are not claims of currently implemented functionality.

---

## 🎯 Project Objective

FINDORA aims to make lost-and-found management more organized, intelligent, secure and accessible within the MIET campus.

By combining explainable AI-based matching, protected ownership verification, anonymous communication and centralized administration, the platform helps connect lost belongings with the people looking for them.

---

<div align="center">

### FINDORA

**Find it. Match it. Return it.**

*Built to make campus item recovery smarter, safer and simpler.*

</div>
