"use client";

import { ArrowUp, ExternalLink, RefreshCw } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { getUserFacingError, sendChatMessage, UserFacingError } from "@/lib/api";
import { safeExternalUrl, timestamp } from "@/lib/format";
import { ChatMessage } from "@/types";

interface ChatBoxProps {
  studentId?: string;
  programId?: string;
  lockedMode?: "rag" | "agent";
  token?: string;
  onStateUpdate?: (stage: string, missingDocs: string[], draftedLetter?: string) => void;
}

export function ChatBox({
  studentId = "std_demo",
  programId = "prog_101",
  lockedMode,
  token,
  onStateUpdate
}: ChatBoxProps) {
  const [mode, setMode] = useState<"rag" | "agent">(lockedMode || "rag");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<UserFacingError | null>(null);
  const [lastSubmitted, setLastSubmitted] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const activeMode = lockedMode || mode;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, error]);

  async function send(text: string, appendUserMessage = true) {
    const clean = text.trim();
    if (!clean || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: clean,
      timestamp: timestamp()
    };

    if (appendUserMessage) setMessages((current) => [...current, userMessage]);
    setInput("");
    setError(null);
    setLastSubmitted(clean);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(clean, activeMode, studentId, programId, token);
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.reply,
        timestamp: timestamp(),
        sources: response.sources,
        application_stage: response.applicationStage,
        missing_documents: response.missingDocs
      };
      setMessages((current) => [...current, assistantMessage]);
      setLastSubmitted(null);

      if (onStateUpdate && (response.applicationStage || response.missingDocs || response.draftedLetter)) {
        onStateUpdate(
          response.applicationStage || "gathering_info",
          response.missingDocs || [],
          response.draftedLetter
        );
      }
    } catch (sendError) {
      setError(getUserFacingError(sendError, activeMode === "rag" ? "AI advisor" : "Application assistant"));
    } finally {
      setIsLoading(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void send(input);
  }

  function changeMode(nextMode: "rag" | "agent") {
    setMode(nextMode);
    setMessages([]);
    setError(null);
    setLastSubmitted(null);
    setInput("");
  }

  return (
    <section className="panel-strong flex min-h-[620px] flex-col" aria-label={activeMode === "rag" ? "AI advisor conversation" : "Application assistant conversation"}>
      <div className="flex flex-col gap-4 border-b border-line p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-serif text-2xl font-semibold">{activeMode === "rag" ? "Ask the document advisor" : "Application assistant"}</h2>
          <p className="mt-1 text-sm text-muted">
            {activeMode === "rag" ? "Answers depend on retrieved university documents." : "Agent tools currently use demonstration records."}
          </p>
        </div>
        {!lockedMode && (
          <div className="flex border border-line" aria-label="Conversation mode">
            <button
              type="button"
              className={`min-h-11 px-3 text-sm font-semibold ${mode === "rag" ? "bg-ink text-paper" : "bg-paper text-ink"}`}
              onClick={() => changeMode("rag")}
              aria-pressed={mode === "rag"}
            >
              Advisor
            </button>
            <button
              type="button"
              className={`min-h-11 border-l border-line px-3 text-sm font-semibold ${mode === "agent" ? "bg-ink text-paper" : "bg-paper text-ink"}`}
              onClick={() => changeMode("agent")}
              aria-pressed={mode === "agent"}
            >
              Application
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto bg-[#f8f5ef] p-5" role="log" aria-live="polite" aria-relevant="additions">
        {messages.length === 0 && (
          <div className="max-w-2xl border-l-4 border-accent bg-paper p-5">
            <p className="font-serif text-xl font-semibold">Start with one precise question.</p>
            <p className="mt-2 text-sm leading-6 text-muted">
              {activeMode === "rag"
                ? "If no document supports the answer, the backend should return that it does not have the information."
                : "Ask about missing documents, a programme deadline, or a motivation-letter draft."}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <article key={message.id} className={`max-w-[92%] border p-4 sm:max-w-[82%] ${message.role === "user" ? "ml-auto border-ink bg-ink text-paper" : "border-quiet bg-paper text-ink"}`}>
            <div className="whitespace-pre-wrap text-sm leading-6">{message.content}</div>
            {message.sources && message.sources.length > 0 && (
              <div className="mt-4 border-t border-quiet pt-4">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Sources returned · {message.sources.length}</p>
                <ul className="mt-3 space-y-3">
                  {message.sources.map((source, index) => {
                    const sourceUrl = safeExternalUrl(source.source_url);
                    return (
                      <li key={`${message.id}-${index}`} className="border-l-2 border-accent pl-3 text-xs leading-5 text-muted">
                        <p>{source.content_snippet}</p>
                        {source.page !== undefined && source.page !== null && <p className="mt-1">Page {source.page}</p>}
                        {sourceUrl && (
                          <a className="mt-2 inline-flex items-center gap-1 font-semibold text-accent underline underline-offset-4" href={sourceUrl} target="_blank" rel="noopener noreferrer">
                            Open source
                            <ExternalLink size={12} aria-hidden="true" />
                          </a>
                        )}
                        {source.source_url && !sourceUrl && <p className="mt-2 font-semibold text-danger">The returned source URL is not a safe web address.</p>}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
            {message.missing_documents && message.missing_documents.length > 0 && (
              <div className="mt-4 border-t border-quiet pt-3 text-xs leading-5">
                Missing documents: {message.missing_documents.join(", ")}
              </div>
            )}
            <time className={`mt-3 block text-[0.68rem] ${message.role === "user" ? "text-[#d8d7d2]" : "text-muted"}`}>{message.timestamp}</time>
          </article>
        ))}

        {isLoading && <p className="text-sm font-semibold text-muted" role="status">Waiting for the backend response</p>}

        {error && (
          <div className="border border-danger bg-paper p-5" role="alert">
            <p className="font-semibold text-danger">{error.title}</p>
            <p className="mt-2 text-sm leading-6 text-muted">{error.message}</p>
            {lastSubmitted && (
              <button type="button" className="button-secondary mt-4" onClick={() => void send(lastSubmitted, false)} disabled={isLoading}>
                <RefreshCw size={15} aria-hidden="true" />
                Retry message
              </button>
            )}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={submit} className="border-t border-line bg-paper p-4">
        <label className="field-label" htmlFor={`chat-input-${activeMode}`}>
          {activeMode === "rag" ? "Question" : "Message to the application agent"}
        </label>
        <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
          <textarea
            id={`chat-input-${activeMode}`}
            className="field min-h-24 resize-y"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={activeMode === "rag" ? "What is the IELTS requirement?" : "What documents am I missing?"}
            maxLength={2000}
          />
          <button type="submit" className="button-primary sm:min-h-24 sm:w-28" disabled={!input.trim() || isLoading}>
            <ArrowUp size={18} aria-hidden="true" />
            {isLoading ? "Sending" : "Send"}
          </button>
        </div>
        <div className="mt-2 flex items-center justify-between gap-3 text-xs text-muted">
          <span>{activeMode === "rag" ? "No external web knowledge is requested by this interface." : "Application submission is not supported."}</span>
          <span>{input.length}/2000</span>
        </div>
      </form>
    </section>
  );
}
