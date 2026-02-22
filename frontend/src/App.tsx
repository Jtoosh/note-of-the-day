import { useCallback, useEffect, useState } from "react";
import "./App.css";

type SnippetPayload = {
  title: string;
  source_file: string;
  breadcrumbs: string[];
  breadcrumbs_text: string;
  text: string;
  continuation: string;
  previous_context: string;
};

function App() {
  const [snippet, setSnippet] = useState<SnippetPayload | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSnippet = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/snippet");
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = (await response.json()) as SnippetPayload;
      setSnippet(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSnippet();
  }, [loadSnippet]);

  return (
    <main className="page">
      <section className="card" aria-live="polite">
        <header className="card-header">
          <p className="eyebrow">Note of the Day</p>
          <h1>{snippet?.title ?? "Loading snippet"}</h1>
        </header>

        {error ? <p className="state error">Could not load snippet: {error}</p> : null}

        {!snippet && !error ? <p className="state">Fetching your snippet...</p> : null}

        {snippet ? (
          <>
            <div className="meta">
              <p>
                <span>Source</span>
                {snippet.source_file}
              </p>
              {snippet.breadcrumbs_text ? (
                <p>
                  <span>Path</span>
                  {snippet.breadcrumbs_text}
                </p>
              ) : null}
            </div>

            {snippet.previous_context ? (
              <blockquote className="context">{snippet.previous_context}</blockquote>
            ) : null}

            <p className="snippet-text">{snippet.text}</p>

            {snippet.continuation ? (
              <p className="continuation">
                <span>Continuation</span>
                {snippet.continuation}
              </p>
            ) : null}
          </>
        ) : null}

        <button type="button" onClick={() => void loadSnippet()} disabled={isLoading}>
          {isLoading ? "Loading..." : "Get New Snippet"}
        </button>
      </section>
    </main>
  );
}

export default App;
