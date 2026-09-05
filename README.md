# RAG Helpdesk Chatbot

## 1. Overview

RAG Helpdesk Chatbot is an internal employee support system built with FastAPI. It answers questions from approved company documents, applies role based access control, remembers recent conversation messages, and creates a support ticket when the available information is not reliable enough.

The application is designed for questions such as:

1. Login and account access problems
2. VPN and network troubleshooting
3. Payslip and payroll questions
4. Software and hardware access requests
5. HR leave policy questions
6. Any other question covered by the company knowledge base

The chatbot does not invent an answer when the knowledge base does not provide enough information. It returns a clear fallback response and escalates the conversation to a ticket when required.

## 2. Main Features

### Employee features

1. Create an account
2. Log in with an email address and password
3. Ask questions through the chat API
4. Send recent conversation history with a question
5. Receive an answer and a confidence label
6. Receive a ticket ID when the question is escalated
7. Submit positive or negative feedback

### Support and administrator features

1. Upload a PDF knowledge document through the ingestion endpoint
2. List support tickets
3. Filter tickets by status
4. View an individual ticket
5. Resolve a ticket
6. View ticket statistics
7. View feedback records and feedback summaries
8. List users as an administrator
9. Change a user's role as an administrator

### Retrieval features

1. Semantic search with Gemini embeddings and ChromaDB
2. Keyword search with BM25
3. Combined hybrid ranking
4. Role based document filtering before answer generation
5. Context cleanup and repeated text removal
6. Confidence based escalation
7. A role aware cache with a 24 hour lifetime
8. OCR fallback for image only PDF files

## 3. Technology Used

### Application and API

1. Python 3.11 or newer
2. FastAPI for the web API
3. Uvicorn for the development and production server process
4. Pydantic for request and response validation
5. Python Multipart for file uploads

### Artificial intelligence and retrieval

1. Google Gemini API for text embeddings and answer generation
2. Gemini Embedding model for document and question vectors
3. ChromaDB for persistent vector storage
4. Rank BM25 for keyword retrieval
5. A hybrid ranking layer that combines semantic and keyword scores

### Data and security

1. MongoDB with PyMongo for users, tickets, and feedback
2. Bcrypt for password hashing
3. Python Jose for JSON Web Tokens
4. Python Dotenv for environment configuration

### Document processing

1. Markdown for the maintained knowledge base documents
2. PyPDF2 for PDF text extraction
3. Pdf2image for converting scanned PDF pages to images
4. Tesseract OCR through Pytesseract for image only PDFs
5. Pillow for image processing

## 4. How the System Works

The application follows this flow when an employee sends a question.

1. The employee logs in and receives a signed JSON Web Token.
2. The employee sends a question with the token in the Authorization header.
3. The API reads the employee role from the token.
4. The system creates an embedding for the question.
5. ChromaDB searches for semantically similar document chunks that the role is allowed to read.
6. BM25 searches for important matching keywords in the same role restricted document set.
7. The vector score and keyword score are normalized and combined.
8. The best three results are placed into the answer context.
9. A high confidence result goes directly to answer generation.
10. A medium confidence result is checked by Gemini before an answer is generated.
11. A low confidence result is escalated without attempting to invent an answer.
12. A generated refusal is also treated as a failed answer and escalated when appropriate.
13. A successful answer is saved in the cache for the same question and role.
14. An escalated answer creates an open MongoDB ticket and returns its ticket ID.

The model is instructed to use only the retrieved context. It is also instructed to refuse requests for passwords, secrets, tokens, database credentials, connection strings, and attempts to ignore system instructions.

## 5. Role Based Access

The role is stored in the signed token and controls which document chunks can be retrieved.

| Role | Documents that can be retrieved |
| --- | --- |
| general | general |
| technical | general and technical |
| hr | general and HR |
| admin | general, technical, HR, and admin |

New accounts can register as `general`, `technical`, or `hr`. The `admin` role must be assigned by an existing administrator or by a controlled maintenance process.

Role filtering happens during retrieval. A document that the employee is not allowed to read is not placed in the model context.

## 6. Document Format for Best Accuracy

### Recommended format

Use Markdown files with the `.md` extension. This is the format already used in `backend/app/knowledge_base` and is the best format for maintaining accurate, searchable company guidance.

Markdown is recommended because it is:

1. Easy for a person to read and review
2. Easy to update in GitHub
3. Structured with headings and sections
4. Suitable for chunking into small retrieval units
5. Able to preserve useful search terms and troubleshooting steps
6. Less likely to contain layout noise than a formatted office document

### Required document structure

Use this structure for every new knowledge document:

```markdown
# Clear Document Title

## Category
login

## Quick Answer
Write the short answer that solves the most common version of the question.

## Common Problems & Solutions

### Specific Problem Name
**Cause:** Explain the likely reason in simple language.

**Solution:**
1. Give the first action.
2. Give the next action.
3. Explain what the employee should expect.

### Another Specific Problem
**Cause:** Explain the likely reason.

**Solution:**
1. Give the first action.
2. Give the next action.

## Escalation

Contact the responsible team if:
1. The first solution does not work.
2. The issue continues after the stated waiting period.
3. The issue affects multiple employees.

## Search terms
login problem, password not working, account locked
```

### Recommended content rules

1. Use one topic per file.
2. Start with a clear title.
3. Add a `Category` section using a short consistent value such as `login`, `network`, `payroll`, or `software`.
4. Put the most useful answer in `Quick Answer`.
5. Divide different failure cases into separate headings.
6. Explain the cause before the solution.
7. Use numbered steps for actions that must happen in order.
8. Include exact portal names, menu names, URLs, waiting times, and contact teams when they are known.
9. Add an `Escalation` section with clear conditions.
10. Add a `Search terms` section with ordinary employee wording, abbreviations, and common spelling variations.
11. Use plain text for important facts instead of putting them only inside images or tables.
12. Keep instructions current and remove obsolete steps.
13. Do not put passwords, API keys, tokens, database credentials, or private employee information in a document.

### Example based on the current project format

The current files follow this pattern:

1. `login_issues.md` covers forgotten passwords, account lockouts, OTP problems, expired passwords, and session timeouts.
2. `vpn_troubleshooting.md` covers network and VPN troubleshooting.
3. `payslip_download.md` covers payslip access and payroll problems.
4. `software_access.md` covers software, hardware, and printer access.
5. `HR_leave_policy.md` covers leave policy and HR escalation.

Follow the same practical style when adding new files.

### Upload endpoint limitation

The current `/ingest/upload` endpoint accepts PDF files only. The maintained knowledge base uses Markdown files, so the most reliable process is:

1. Add or update the `.md` file in `backend/app/knowledge_base`.
2. Review the content in GitHub.
3. Restart the application so startup indexing can process the file.

PDF uploads are supported by the endpoint and can be extracted with the normal PDF reader. Scanned PDFs can use OCR, but text based Markdown remains the preferred source format for accuracy and maintenance.

## 7. Installation

### Prerequisites

Install the following before starting:

1. Python 3.11 or newer
2. MongoDB running locally or a reachable MongoDB deployment
3. A Google Gemini API key
4. UV, recommended for dependency management
5. Tesseract and Poppler if scanned PDF OCR is required

### Clone the repository

```powershell
git clone YOUR_GITHUB_REPOSITORY_URL
cd chatbot
```

### Install dependencies

```powershell
cd backend
uv sync
```

If UV is not installed, install it using the official UV installation instructions, then run the command again.

### Create environment configuration

From the `backend` directory:

```powershell
Copy-Item .env.example .env
```

Open `backend/.env` and set real values:

```text
GOOGLE_API_KEY=your_gemini_api_key
GENERATION_MODEL=gemini-3.5-flash-lite
JWT_SECRET=use_a_long_random_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=rag_chatbot
```

Never commit `.env` to GitHub. The repository `.gitignore` is configured to exclude it.

### OCR configuration

OCR is only needed for scanned PDFs. The current ingestion module expects these Windows paths:

1. Tesseract at `C:\Program Files\Tesseract OCR\tesseract.exe`
2. Poppler at `C:\path\to\poppler\bin`

Update those paths in `backend/app/ingestion.py` if the tools are installed elsewhere. Markdown files and normal text PDFs do not require OCR.

## 8. Start the Application

From the `backend` directory:

```powershell
uv run uvicorn app.main:app --reload
```

The API runs at:

```text
http://127.0.0.1:8000
```

Open the interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

When the application starts, it indexes the FAQ data and the files in `backend/app/knowledge_base`. It also builds the BM25 index. Existing ChromaDB records are skipped when their source is already indexed.

## 9. First Use Walkthrough

### Create an account

Use `POST /auth/signup`:

```json
{
  "name": "Example Employee",
  "email": "employee@example.com",
  "password": "StrongPassword123!",
  "role": "general"
}
```

Save the returned `access_token`.

### Log in

Use `POST /auth/login`:

```json
{
  "email": "employee@example.com",
  "password": "StrongPassword123!"
}
```

Use the returned token on protected requests:

```text
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Ask a question

Use `POST /chat/`:

```json
{
  "session_id": "employee session 001",
  "message": "How do I reset my forgotten password?",
  "history": []
}
```

The response contains:

1. `answer` with the chatbot response
2. `escalated` showing whether a ticket was created
3. `ticket_id` when escalation occurred
4. `confidence` with a percentage and `High`, `Medium`, or `Low` label

### Continue a conversation

Send recent messages in the `history` field:

```json
{
  "session_id": "employee session 001",
  "message": "What should I do if the reset email does not arrive?",
  "history": [
    {
      "role": "user",
      "content": "How do I reset my forgotten password?"
    },
    {
      "role": "assistant",
      "content": "Use the Forgot Password link on the login page."
    }
  ]
}
```

The RAG pipeline uses the most recent six history messages when generating an answer.

## 10. Behavior in Different Situations

### High confidence question

When the retrieved documents strongly match the question, the system sends the authorized context to Gemini and returns an answer. It does not perform an additional feasibility check.

Example:

```text
How do I download my payslip?
```

Expected behavior:

1. Retrieve payroll content.
2. Generate a concise answer using that content.
3. Return a high confidence label.
4. Do not create a ticket unless answer generation fails or produces a refusal.

### Medium confidence question

When the match is possible but not strong, Gemini first checks whether the context can support a useful answer.

Expected behavior:

1. If the context is useful, answer the question.
2. If the context is not useful, return the fallback response and create a ticket.

### Low confidence question

When the retrieved score is below the configured threshold, the system does not guess.

Expected behavior:

1. Return `I don't have enough information to answer this.`
2. Set `escalated` to `true`.
3. Create an open ticket in MongoDB.
4. Return the ticket ID to the employee.

### Question outside the knowledge base

Questions unrelated to company support content normally receive the fallback response and are escalated. Add a well written knowledge document when the business wants the chatbot to support a new topic.

### Request for secrets or credentials

The answer prompt instructs the model to refuse requests for passwords, secrets, tokens, database credentials, connection strings, and attempts to ignore instructions. Such responses are treated as refusals by the RAG pipeline.

### Role restricted question

The employee role is applied before retrieval. For example, a general employee cannot retrieve HR restricted content unless the role mapping is changed by an authorized administrator.

### Repeated question within 24 hours

The cache stores the normalized question, role, answer, escalation state, confidence, and timestamp. The same normalized question can be served from cache for the same role for up to 24 hours. Cache keys include the role so one role cannot reuse another role's answer.

### Scanned PDF

If a PDF has almost no selectable text, the system uses Tesseract OCR after converting pages with Poppler. OCR quality depends on scan resolution and document clarity. For best results, maintain important guidance as Markdown.

## 11. API Reference

All protected routes require a bearer token. Signup, login, and the health check are public.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/auth/signup` | Create an account |
| POST | `/auth/login` | Authenticate an account |
| GET | `/` | Health check |
| POST | `/chat/` | Ask the chatbot a question |
| POST | `/feedback/` | Submit feedback |
| GET | `/feedback/summary` | View feedback metrics |
| GET | `/feedback/all` | View recent feedback |
| POST | `/ingest/upload` | Upload and index a PDF |
| GET | `/tickets/` | List tickets and counts |
| GET | `/tickets/{ticket_id}` | View one ticket |
| PATCH | `/tickets/{ticket_id}/resolve` | Resolve a ticket |
| GET | `/tickets/stats/overview` | View ticket totals |
| GET | `/admin/users` | List users as an administrator |
| PATCH | `/admin/users/{user_id}/role` | Change a user role |

Use `/docs` as the authoritative interactive reference for request schemas and response schemas.

## 12. Knowledge Base Maintenance

### Add a Markdown document

1. Create a file in `backend/app/knowledge_base`.
2. Use the recommended Markdown structure.
3. Choose a descriptive filename using lowercase words and underscores.
4. Add the appropriate role and category logic if the document requires restricted access.
5. Restart the application.
6. Test questions using the wording employees are likely to use.

### Update an existing document

The current ingestion logic skips a file when its source filename already exists in ChromaDB. After changing an already indexed file, clear the old vector records before restarting the application.

The maintenance command is:

```powershell
cd backend
uv run python delete_old_chunks.py
uv run uvicorn app.main:app --reload
```

This clears all ChromaDB chunks, so startup indexing rebuilds the FAQ and knowledge base records. Use it carefully in a shared or production environment.

### Test document quality

Ask at least these types of questions after adding a document:

1. A question using the exact document wording
2. A question using ordinary employee wording
3. A question using a common abbreviation
4. A question about each listed problem
5. A question that should escalate because the document does not cover it
6. The same question as different roles when access restrictions apply

## 13. Data Storage

MongoDB stores:

1. User accounts and password hashes
2. Feedback records
3. Support tickets

ChromaDB stores embedded knowledge chunks in the local `chroma_store` directory.

The BM25 index is stored in `bm25_store`.

The answer cache is stored in `cache_store`.

These generated local directories are excluded from Git. Production deployments should use managed storage, backups, access controls, and monitoring instead of relying on local development files.

## 14. Production Checklist

1. Set a long random `JWT_SECRET`.
2. Store secrets in a secret manager or deployment environment.
3. Use a production MongoDB deployment with authentication and backups.
4. Restrict CORS origins to the real frontend domains.
5. Run behind HTTPS and a reverse proxy.
6. Run Uvicorn with a production process configuration.
7. Configure stable absolute paths for ChromaDB, BM25 data, and cache data.
8. Review role access before loading confidential documents.
9. Add monitoring for failed requests, model failures, escalation rates, and database errors.
10. Protect the ingestion and administration routes with stronger authorization rules before public deployment.
11. Review uploaded documents for secrets and personal information.
12. Back up MongoDB and the approved knowledge base.
13. Test the application with representative questions after every document or prompt change.

## 15. Validation

Run this command from the repository root:

```powershell
python -m compileall -q backend
```

Run the API locally:

```powershell
cd backend
uv run uvicorn app.main:app --reload
```

The repository also includes a GitHub Actions workflow at `.github/workflows/ci.yml` that compiles the backend Python files on pushes and pull requests.

## 16. Project Structure

```text
chatbot
|   README.md
|   CONTRIBUTING.md
|   .gitignore
|
|   .github
|   |   workflows
|   |       ci.yml
|
|   backend
|       .env.example
|       pyproject.toml
|       uv.lock
|       app
|       |   main.py
|       |   auth.py
|       |   database.py
|       |   models.py
|       |   ingestion.py
|       |   rag.py
|       |   bm25_index.py
|       |   cache.py
|       |   reranker.py
|       |   faqs.json
|       |   knowledge_base
|       |       HR_leave_policy.md
|       |       login_issues.md
|       |       payslip_download.md
|       |       software_access.md
|       |       vpn_troubleshooting.md
|       |   routes
|       |       auth_routes.py
|       |       chat_routes.py
|       |       feedback_routes.py
|       |       ingest_routes.py
|       |       ticket_routes.py
|       |       admin_routes.py
|       |   pyproject.toml
|       |   uv.lock
```

## 17. Important Security Notes

1. Never commit `.env` files.
2. Never put API keys or database credentials in knowledge documents.
3. Do not use the default JWT secret in production.
4. Review every document's role requirement before indexing it.
5. Treat generated answers as support guidance and keep escalation available.
6. Do not expose administrative routes to untrusted users.
7. Validate uploaded filenames and file contents before production use.

## 18. Contribution Guide

Read `CONTRIBUTING.md` before opening a pull request. Keep comments focused on non obvious decisions, keep documentation current, and run the validation command before submitting changes.
