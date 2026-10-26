import { useState } from "react";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

const INITIAL_FORM = {
  host: "",
  port: "3306",
  database: "",
  username: "",
  password: "",
};

async function readResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "The request failed. Please check your details and try again."
    );
  }

  return data;
}

export default function DatabaseConnection({ onConnectionChange }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [connection, setConnection] = useState(null);
  const [connectedDetails, setConnectedDetails] = useState(null);

  function clearConnectionState() {
    setConnection(null);
    setConnectedDetails(null);
    onConnectionChange?.(null);
  }

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));

    clearConnectionState();
    setError("");
  }

  async function testConnection(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    clearConnectionState();

    const payload = {
      ...form,
      host: form.host.trim(),
      database: form.database.trim(),
      username: form.username.trim(),
      port: Number(form.port),
    };

    try {
      const response = await fetch(
        `${API_URL}/api/connections/test`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await readResponse(response);

      setConnection(data);
      setConnectedDetails(payload);

      // Share the successful connection with App.jsx.
      onConnectionChange?.({
        details: payload,
        database: data.database,
        tableCount: data.table_count,
      });
    } catch (err) {
      setError(
        err.message ||
          "Could not reach QueryPilot AI. Check the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  function disconnectDatabase() {
    setForm(INITIAL_FORM);
    setError("");
    setConnection(null);
    setConnectedDetails(null);

    // Tell App.jsx that the database is disconnected.
    onConnectionChange?.(null);
  }

  return (
    <section className="connection-panel">
      <h2>Connect Your MySQL Database</h2>

      <p>
        Connect an existing MySQL database to explore its tables
        and ask questions in plain English. Your database remains
        on its own server.
      </p>

      <p>
        Use a database account with{" "}
        <strong>read-only permissions</strong>. Your database server
        must be reachable from the QueryPilot backend.
      </p>

      <form onSubmit={testConnection}>
        <label htmlFor="mysql-host">
          Database host
          <input
            id="mysql-host"
            name="host"
            value={form.host}
            onChange={handleChange}
            placeholder="e.g. mysql.example.com"
            autoComplete="off"
            required
            maxLength={255}
          />
        </label>

        <label htmlFor="mysql-port">
          Port
          <input
            id="mysql-port"
            name="port"
            type="number"
            min="1"
            max="65535"
            value={form.port}
            onChange={handleChange}
            required
          />
        </label>

        <label htmlFor="mysql-database">
          Database name
          <input
            id="mysql-database"
            name="database"
            value={form.database}
            onChange={handleChange}
            placeholder="e.g. analytics"
            autoComplete="off"
            required
            maxLength={64}
          />
        </label>

        <label htmlFor="mysql-username">
          Username
          <input
            id="mysql-username"
            name="username"
            value={form.username}
            onChange={handleChange}
            placeholder="Your MySQL username"
            autoComplete="off"
            required
            maxLength={128}
          />
        </label>

        <label htmlFor="mysql-password">
          Password
          <input
            id="mysql-password"
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            autoComplete="new-password"
            required
          />
        </label>

        <button
          type="submit"
          disabled={loading}
        >
          {loading ? "Testing connection..." : "Test Connection"}
        </button>
      </form>

      {error && (
        <p className="connection-error" role="alert">
          {error}
        </p>
      )}

      {connection && connectedDetails && (
        <div className="schema-preview" aria-live="polite">
          <h3>Database connected successfully</h3>

          <p>
            Database: <strong>{connection.database}</strong>
          </p>

          <p>
            Tables found: <strong>{connection.table_count}</strong>
          </p>

          {connection.schema?.length > 0 ? (
            connection.schema.map((table) => (
              <details key={table.table}>
                <summary>{table.table}</summary>

                <ul>
                  {table.columns.map((column) => (
                    <li key={column.name}>
                      <strong>{column.name}</strong>
                      {" — "}
                      {column.type}
                      {column.nullable ? " (nullable)" : ""}
                    </li>
                  ))}
                </ul>
              </details>
            ))
          ) : (
            <p>
              The connection succeeded, but no tables were discovered.
            </p>
          )}

          <button
            type="button"
            onClick={disconnectDatabase}
          >
            Disconnect
          </button>
        </div>
      )}
    </section>
  );
}