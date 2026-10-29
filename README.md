
# QueryPilot AI

**Ask questions about your database in plain English. Get SQL queries and data-driven answers.**

QueryPilot AI is an AI-powered database analyst that converts natural-language questions into SQL queries, validates the generated SQL, executes permitted read queries against a connected MySQL database, and displays the results in a web interface.

Instead of manually writing SQL for every question, users can ask questions in everyday English and explore their data more easily.

## Live Demo

- **Frontend:** https://query-pilot-ai-eight.vercel.app/
- **Backend API:** https://querypilot-ai-jbht.onrender.com
- **API Documentation:** https://querypilot-ai-jbht.onrender.com/docs

## Features

- **Natural Language to SQL:** Convert plain-English questions into SQL using Groq-powered AI.
- **MySQL Database Connectivity:** Connect to an existing MySQL database using connection details.
- **SQL Safety Validation:** Validate generated SQL using SQLGlot and application-level rules before execution.
- **Read-Only Query Workflow:** Retrieve data using permitted SQL queries without requiring database modification privileges.
- **Live Query Results:** View generated SQL and query results in the web interface.
- **Schema-Aware Generation:** Inspect database tables and columns to provide context for SQL generation.
- **Secure Database Connections:** Verify TLS certificates for remote MySQL connections.
- **Cloud Deployment:** Deploy the frontend on Vercel and the backend on Render.

## How It Works

1. **Connect:** Enter the connection details for an existing MySQL database.
2. **Discover Schema:** Validate the connection and retrieve database table and column information.
3. **Ask a Question:** Submit a question in natural language.
4. **Generate SQL:** The backend sends the question and database schema context to the Groq AI service.
5. **Validate SQL:** SQLGlot parses the generated query, and application-level rules check whether it is permitted.
6. **Execute Query:** Execute the validated SQL against the connected database.
7. **Display Results:** Show the generated SQL and query results in the frontend.

## Architecture

```text
React + Vite Frontend
        |
        | HTTP / JSON
        v
FastAPI Backend
        |
        +------> Groq AI API
        |        SQL Generation
        |
        +------> SQLGlot
        |        SQL Validation
        |
        +------> MySQL Database
                 Query Execution
```

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI, Uvicorn |
| AI Integration | Groq API |
| Database | MySQL |
| Database Connectivity | SQLAlchemy, PyMySQL |
| SQL Parsing | SQLGlot |
| Configuration | Environment variables, python-dotenv |
| Frontend Deployment | Vercel |
| Backend Deployment | Render |

## Project Structure

```text
QueryPilot-AI/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── ai_service.py
│   │   ├── connections.py
│   │   ├── database.py
│   │   └── sql_validator.py
│   ├── certs/
│   │   └── ca.pem
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── index.html
├── .gitignore
└── README.md
```

*This is a simplified representation of the main project files.*

## Getting Started

### Prerequisites

- Python 3.12 or a compatible Python version
- Node.js and npm
- An accessible MySQL database
- A Groq API key

### 1. Clone the Repository

```bash
git clone https://github.com/BimalSinha59/QueryPilot-AI.git
cd QueryPilot-AI
```

### 2. Set Up the Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Backend Environment Variables

Create a `.env` file inside the `backend` directory:

```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=your_application_database_url
AI_DATABASE_URL=your_ai_database_url
MYSQL_SSL_CA=certs/ca.pem
```

### 4. Start the Backend

From the `backend` directory:

```bash
python -m uvicorn app.main:app --reload
```

The backend should be available at:

- API: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/api/health

### 5. Set Up the Frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Create a `.env` file inside the `frontend` directory:

```env
VITE_API_URL=http://127.0.0.1:8000
```


### 6. Start the Frontend

```bash
npm run dev
```

Open the local URL printed by Vite, usually:

http://localhost:5173


## SQL Safety

QueryPilot AI validates AI-generated SQL before execution.

The current SQL validator includes these restrictions:

- Only a single `SELECT` statement is permitted.
- Referenced tables must belong to the connected database's table allowlist.
- Database-qualified table names are rejected.
- JOIN operations and nested queries are currently rejected.
- `SELECT INTO` and locking clauses are rejected.
- An explicit numeric `LIMIT` between 1 and 100 is required.

These restrictions help control which queries can execute but may reject some otherwise valid analytical queries.


## Current Limitations

- MySQL is the database engine supported by the current connection workflow.
- JOINs and nested queries are rejected by the current SQL validator.
- AI-generated SQL may be incorrect even when it passes validation.
- Query results depend on the database schema, data quality, permissions, and available resources.
- Additional security work is needed before treating the deployment as production-ready for untrusted users.

## Future Improvements

- Safely support analytical JOINs and subqueries.
- Provide clearer SQL validation errors.
- Explain generated SQL in simple language.
- Add query history and saved questions.
- Improve result visualization and pagination.
- Add authentication and per-user access controls.
- Implement rate limiting, monitoring, and stronger network egress protections.

## Contributing

Suggestions, bug reports, and contributions are welcome. For significant changes, consider opening an issue before submitting a pull request.


---

**QueryPilot AI — making database analytics more accessible through natural language.**
