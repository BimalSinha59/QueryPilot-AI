import { useState } from "react";
import "./index.css";
import DatabaseConnection from "./DatabaseConnection";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

const EXAMPLES = [
  {
    title: "Explore my data",
    question: "Show me 10 sample records from my database.",
    icon: "⌕",
  },
  {
    title: "Find patterns",
    question: "Identify the main trends in my data.",
    icon: "↗",
  },
  {
    title: "Compare values",
    question: "Compare the average values across categories.",
    icon: "⇄",
  },
  {
    title: "Summarize results",
    question: "Give me a summary of my data.",
    icon: "▤",
  },
];

function formatValue(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function App() {
  const [databaseConnection, setDatabaseConnection] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [askError, setAskError] = useState("");

  const isConnected = Boolean(databaseConnection?.details);

  function handleConnectionChange(connection) {
    setDatabaseConnection(connection);
    setAnswer(null);
    setAskError("");
  }

  async function askQuestion(event) {
    event.preventDefault();

    if (!isConnected || loading) return;

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setAskError("Please enter a question.");
      return;
    }

    setLoading(true);
    setAskError("");
    setAnswer(null);

    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmedQuestion,
          connection: databaseConnection.details,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Your question could not be processed."
        );
      }

      setAnswer(data);
    } catch (error) {
      setAskError(
        error.message || "Could not connect to QueryPilot AI."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleExampleClick(example) {
    setQuestion(example);
    setAskError("");
  }

  return (
    <main className="app-container">
      <header className="app-header">
        <a className="brand" href="/" aria-label="QueryPilot AI home">
          <span className="brand-icon">Q</span>
          <span>
            QueryPilot <span className="brand-light">AI</span>
          </span>
        </a>

        <span className="header-label">
          YOUR AI DATA ANALYST
        </span>
      </header>

      <section className="hero-section">
        <div className="hero-badge">
          <span className="status-dot" />
          YOUR DATA. YOUR QUESTIONS.
        </div>

        <h1>
          Make your data
          <span className="hero-gradient"> speak for itself.</span>
        </h1>

        <p className="hero-description">
          Connect your MySQL database, ask questions in plain English,
          and get answers backed by SQL and real query results.
        </p>
      </section>

      <section className="connection-section" id="database-connection">
        <div className="section-heading">
          <span className="step-label">STEP 01</span>
          <h2>Connect your database</h2>
          <p>
            Connect to your own MySQL database to get started.
          </p>
        </div>

        <DatabaseConnection
          onConnectionChange={handleConnectionChange}
        />
      </section>

      <section className="ai-section">
        <div className="section-heading">
          <span className="step-label">STEP 02</span>
          <h2>What would you like to know?</h2>
          <p>
            Ask a question about your connected data. QueryPilot will
            generate SQL and return the matching results.
          </p>
        </div>

        <form onSubmit={askQuestion} className="question-form">
          <label htmlFor="question">Ask a question</label>

          <textarea
            id="question"
            value={question}
            onChange={(event) => {
              setQuestion(event.target.value);
              setAskError("");
            }}
            placeholder={
              isConnected
                ? "e.g. Show the top 10 products by total sales..."
                : "Connect your database in Step 01 to start asking questions."
            }
            rows={4}
            maxLength={1000}
            disabled={!isConnected || loading}
          />

          <div className="question-form-footer">
            <span className="character-count">
              {question.length}/1000
            </span>

            <button
              type="submit"
              disabled={!isConnected || loading || !question.trim()}
              className="primary-button"
              title={
                !isConnected
                  ? "Connect your database first"
                  : "Ask QueryPilot AI"
              }
            >
              {loading ? (
                <>
                  <span className="loading-spinner" />
                  Analyzing...
                </>
              ) : (
                <>
                  Ask QueryPilot <span aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>
        </form>

        {!isConnected && (
          <p className="muted-text connection-hint">
            Connect your database above to enable questions and examples.
          </p>
        )}

        <div className="examples">
          <p className="examples-heading">Need some inspiration?</p>

          <div className="examples-grid">
            {EXAMPLES.map((example) => (
              <button
                type="button"
                className="example-card"
                key={example.title}
                onClick={() => handleExampleClick(example.question)}
                disabled={!isConnected || loading}
              >
                <span className="example-icon">{example.icon}</span>

                <span className="example-card-text">
                  <strong>{example.title}</strong>
                  <span>{example.question}</span>
                </span>

                <span className="example-arrow" aria-hidden="true">
                  ↗
                </span>
              </button>
            ))}
          </div>
        </div>

        {askError && (
          <div className="error-message" role="alert">
            <strong>Something went wrong</strong>
            <p>{askError}</p>
          </div>
        )}

        {answer && (
          <section className="answer-section" aria-live="polite">
            <div className="answer-heading">
              <div>
                <span className="step-label">QUERY COMPLETE</span>
                <h3>Your results</h3>
              </div>

              <span className="result-count">
                {answer.row_count ?? answer.rows?.length ?? 0} rows
              </span>
            </div>

            <div className="question-summary">
              <strong>Your question</strong>
              <p>{answer.question}</p>
            </div>

            {!answer.rows?.length ? (
              <p className="muted-text">
                The query completed successfully, but no rows were returned.
              </p>
            ) : (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      {(answer.columns || []).map((column) => (
                        <th key={column}>
                          {column.replaceAll("_", " ")}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {answer.rows.map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {(answer.columns || []).map((column) => (
                          <td key={column}>
                            {formatValue(row[column])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <details className="sql-details">
              <summary>
                <span>View generated SQL</span>
                <span className="sql-summary-hint">
                  Inspect the query
                </span>
              </summary>

              <pre>
                <code>{answer.sql}</code>
              </pre>
            </details>
          </section>
        )}
      </section>

      <footer className="app-footer">
        <a className="footer-brand" href="/">
          QueryPilot AI
        </a>
        <span>Natural language. Real SQL. Clear answers.</span>
      </footer>
    </main>
  );
}

export default App;