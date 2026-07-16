import { useEffect, useState } from "react";
import { BookOpen, FileText } from "lucide-react";
import {
  fetchExternalDoc,
  fetchExternalDocs,
  type ExternalDocRecord,
  type ExternalDocSummaryRecord,
} from "../api";

export default function DocsPage() {
  const [docs, setDocs] = useState<ExternalDocSummaryRecord[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<ExternalDocRecord | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDoc, setLoadingDoc] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDocs() {
      try {
        setLoadingList(true);
        setError(null);
        const nextDocs = await fetchExternalDocs();
        if (cancelled) return;
        setDocs(nextDocs);
        setSelectedSlug(nextDocs[0]?.slug ?? null);
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load docs");
        }
      } finally {
        if (!cancelled) {
          setLoadingList(false);
        }
      }
    }

    void loadDocs();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedSlug) {
      setSelectedDoc(null);
      return;
    }

    let cancelled = false;

    async function loadDoc() {
      try {
        setLoadingDoc(true);
        setError(null);
        const doc = await fetchExternalDoc(selectedSlug);
        if (!cancelled) {
          setSelectedDoc(doc);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load doc");
        }
      } finally {
        if (!cancelled) {
          setLoadingDoc(false);
        }
      }
    }

    void loadDoc();
    return () => {
      cancelled = true;
    };
  }, [selectedSlug]);

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="mb-6">
        <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">IN-APP HELP</div>
        <h1 className="text-xl font-mono font-semibold text-foreground">Documentation</h1>
        <p className="text-[10px] font-mono text-muted-foreground mt-1">
          External docs are served through the API so the same content can back local help and future hosted help.
        </p>
      </div>

      {error && (
        <div className="border border-red-400/25 rounded-sm bg-red-400/10 px-4 py-4 mb-5">
          <div className="text-[10px] font-mono text-red-300">Docs API error</div>
          <div className="text-[10px] font-mono text-red-200/80 mt-1 break-words">{error}</div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-5">
        <aside className="border border-border bg-card rounded-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-border text-[9px] font-mono tracking-widest text-muted-foreground">
            AVAILABLE GUIDES
          </div>
          {loadingList ? (
            <div className="px-4 py-5 text-[10px] font-mono text-muted-foreground">Loading docs...</div>
          ) : docs.length === 0 ? (
            <div className="px-4 py-5 text-[10px] font-mono text-muted-foreground">No docs found.</div>
          ) : (
            <div className="p-2 space-y-1">
              {docs.map((doc) => (
                <button
                  key={doc.slug}
                  type="button"
                  onClick={() => setSelectedSlug(doc.slug)}
                  className={`w-full text-left px-3 py-2 rounded-sm border transition-colors ${
                    selectedSlug === doc.slug
                      ? "bg-[#00c9a7]/10 border-[#00c9a7]/25 text-[#00c9a7]"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-3.5 h-3.5 flex-shrink-0" />
                    <span className="text-[10px] font-mono">{doc.title}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </aside>

        <section className="border border-border bg-card rounded-sm">
          <div className="px-4 py-3 border-b border-border flex items-center gap-2">
            <FileText className="w-3.5 h-3.5 text-[#00c9a7]" />
            <div className="text-[10px] font-mono text-foreground">
              {selectedDoc?.title ?? "Select a guide"}
            </div>
          </div>
          <div className="px-5 py-4">
            {loadingDoc ? (
              <div className="text-[10px] font-mono text-muted-foreground">Loading document...</div>
            ) : selectedDoc ? (
              <pre className="whitespace-pre-wrap text-[10px] leading-6 font-mono text-muted-foreground">
                {selectedDoc.content}
              </pre>
            ) : (
              <div className="text-[10px] font-mono text-muted-foreground">Choose a document from the left.</div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
