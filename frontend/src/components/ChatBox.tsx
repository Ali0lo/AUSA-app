"use client";

import { ArrowUp, ExternalLink, Paperclip, RefreshCw, X } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { getUserFacingError, sendChatMessage, uploadDocumentAndChat, UserFacingError } from "@/lib/api";
import { safeExternalUrl, timestamp } from "@/lib/format";
import { useLanguage } from "@/lib/i18n";
import { ChatMessage, StudentProfile } from "@/types";

interface ChatBoxProps {
  studentId?: string;
  programId?: string;
  lockedMode?: "rag" | "agent";
  token?: string;
  onStateUpdate?: (stage: string, missingDocs: string[], draftedLetter?: string) => void;
  onProfileUpdate?: (updatedProfile: Partial<StudentProfile>) => void;
}

function StreamingMessageContent({
  content,
  isStreaming,
  onFinish
}: {
  content: string;
  isStreaming?: boolean;
  onFinish?: () => void;
}) {
  const [displayedLength, setDisplayedLength] = useState(() => (
    isStreaming && process.env.NODE_ENV !== "test" ? 0 : content.length
  ));

  useEffect(() => {
    if (!isStreaming || process.env.NODE_ENV === "test") {
      return;
    }

    const interval = setInterval(() => {
      setDisplayedLength((current) => {
        const step = Math.max(2, Math.ceil(content.length / 50));
        const next = Math.min(content.length, current + step);
        if (next >= content.length) {
          clearInterval(interval);
          onFinish?.();
        }
        return next;
      });
    }, 16);

    return () => clearInterval(interval);
  }, [content, isStreaming, onFinish]);

  const isDone = !isStreaming || displayedLength >= content.length || process.env.NODE_ENV === "test";
  const displayedText = isDone ? content : content.slice(0, displayedLength);

  return (
    <div className="whitespace-pre-wrap text-sm leading-6">
      {displayedText}
      {!isDone && (
        <span
          className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-accent align-middle"
          aria-hidden="true"
        />
      )}
    </div>
  );
}

export function ChatBox({
  studentId = "std_demo",
  programId = "prog_101",
  lockedMode,
  token,
  onStateUpdate,
  onProfileUpdate
}: ChatBoxProps) {
  const { t } = useLanguage();
  const [mode, setMode] = useState<"rag" | "agent">(lockedMode || "rag");
  const [input, setInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<UserFacingError | null>(null);
  const [lastSubmitted, setLastSubmitted] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const activeMode = lockedMode || mode;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, error]);

  async function send(text: string, appendUserMessage = true) {
    const clean = text.trim();
    if ((!clean && !selectedFile) || isLoading) return;

    const displayContent = selectedFile
      ? `${clean ? clean + "\n" : ""}[Attached Document: ${selectedFile.name}]`
      : clean;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: displayContent,
      timestamp: timestamp(),
      attachment_name: selectedFile?.name
    };

    if (appendUserMessage) setMessages((current) => [...current, userMessage]);
    setInput("");
    setError(null);
    setLastSubmitted(clean);
    setIsLoading(true);

    try {
      let response;
      if (selectedFile) {
        response = await uploadDocumentAndChat(selectedFile, clean, studentId, programId, token);
      } else {
        response = await sendChatMessage(clean, activeMode, studentId, programId, token);
      }

      const assistantId = `assistant-${Date.now()}`;
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: response.reply,
        timestamp: timestamp(),
        sources: response.sources,
        application_stage: response.applicationStage,
        missing_documents: response.missingDocs
      };
      setStreamingMessageId(assistantId);
      setMessages((current) => [...current, assistantMessage]);
      setLastSubmitted(null);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";

      if (onStateUpdate && (response.applicationStage || response.missingDocs || response.draftedLetter)) {
        onStateUpdate(
          response.applicationStage || "gathering_info",
          response.missingDocs || [],
          response.draftedLetter
        );
      }

      if (onProfileUpdate && response.updatedProfile) {
        onProfileUpdate(response.updatedProfile);
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
    setSelectedFile(null);
  }

  return (
    <section className="panel-strong flex min-h-[620px] flex-col overflow-hidden shadow-2xl" aria-label={activeMode === "rag" ? "AI advisor conversation" : "Application assistant conversation"}>
      <div className="flex flex-col gap-4 border-b border-white/10 bg-[#13152c]/90 p-5 backdrop-blur-xl sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-serif text-2xl font-semibold text-white">{activeMode === "rag" ? t("askDocumentAdvisor") : t("applicationAssistant")}</h2>
          <p className="mt-1 text-sm text-slate-400">
            {activeMode === "rag" ? t("advisorSubtext") : t("applicationAssistantDesc")}
          </p>
        </div>
        {!lockedMode && (
          <div className="flex rounded-full border border-white/10 bg-white/[0.04] p-1 backdrop-blur-md" aria-label="Conversation mode">
            <button
              type="button"
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-all ${
                mode === "rag"
                  ? "bg-gradient-to-r from-[#FF7A00] to-[#FF4500] text-white shadow-md shadow-orange-500/20"
                  : "text-slate-300 hover:text-white"
              }`}
              onClick={() => changeMode("rag")}
              aria-pressed={mode === "rag"}
            >
              {t("advisorModeRag")}
            </button>
            <button
              type="button"
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-all ${
                mode === "agent"
                  ? "bg-gradient-to-r from-[#FF7A00] to-[#FF4500] text-white shadow-md shadow-orange-500/20"
                  : "text-slate-300 hover:text-white"
              }`}
              onClick={() => changeMode("agent")}
              aria-pressed={mode === "agent"}
            >
              {t("advisorModeAgent")}
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto bg-[#0a0c1a]/70 p-5 backdrop-blur-sm" role="log" aria-live="polite" aria-relevant="additions">
        {messages.length === 0 && (
          <div className="max-w-2xl rounded-2xl border border-white/10 border-l-4 border-l-accent bg-white/[0.03] p-5 backdrop-blur-md">
            <p className="font-serif text-xl font-semibold text-white">Start with one precise question or upload a document.</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {activeMode === "rag"
                ? "Answers are grounded strictly in official university admission and scholarship guidelines."
                : "Ask about missing documents, deadlines, or attach your transcript/certificate PDF to auto-update your profile."}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <article
            key={message.id}
            className={`max-w-[92%] rounded-2xl p-4 sm:max-w-[82%] ${
              message.role === "user"
                ? "ml-auto border border-orange-500/30 bg-gradient-to-r from-[#FF7A00] to-[#FF4500] text-white shadow-lg shadow-orange-500/10"
                : "border border-white/10 bg-white/[0.05] text-slate-100 shadow-xl backdrop-blur-md"
            }`}
          >
            {message.role === "assistant" ? (
              <StreamingMessageContent
                content={message.content}
                isStreaming={streamingMessageId === message.id}
                onFinish={() => setStreamingMessageId(null)}
              />
            ) : (
              <div className="whitespace-pre-wrap text-sm leading-6">{message.content}</div>
            )}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-4 border-t border-white/10 pt-4">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">{t("sourcesReturned")} · {message.sources.length}</p>
                <ul className="mt-3 space-y-3">
                  {message.sources.map((source, index) => {
                    const sourceUrl = safeExternalUrl(source.source_url);
                    return (
                      <li key={`${message.id}-${index}`} className="rounded-xl border border-white/10 border-l-2 border-l-accent bg-white/[0.02] p-3 text-xs leading-5 text-slate-300">
                        <p>{source.content_snippet}</p>
                        {source.page !== undefined && source.page !== null && <p className="mt-1 font-mono text-[0.7rem] text-slate-400">Page {source.page}</p>}
                        {sourceUrl && (
                          <a className="mt-2 inline-flex items-center gap-1 font-semibold text-accent underline underline-offset-4 hover:text-orange-400" href={sourceUrl} target="_blank" rel="noopener noreferrer">
                            {t("openSource")}
                            <ExternalLink size={12} aria-hidden="true" />
                          </a>
                        )}
                        {source.source_url && !sourceUrl && <p className="mt-2 font-semibold text-rose-400">The returned source URL is not a safe web address.</p>}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
            {message.missing_documents && message.missing_documents.length > 0 && (
              <div className="mt-4 border-t border-white/10 pt-3 text-xs leading-5 text-slate-300">
                Missing documents: {message.missing_documents.join(", ")}
              </div>
            )}
            <time className={`mt-3 block text-[0.68rem] ${message.role === "user" ? "text-orange-100/75" : "text-slate-400"}`}>{message.timestamp}</time>
          </article>
        ))}

        {isLoading && (
          <div className="max-w-[92%] rounded-2xl border border-white/10 bg-white/[0.05] p-4 text-slate-200 backdrop-blur-md sm:max-w-[82%]" role="status">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-accent animate-bounce [animation-delay:-0.3s]" />
              <span className="h-2 w-2 rounded-full bg-accent animate-bounce [animation-delay:-0.15s]" />
              <span className="h-2 w-2 rounded-full bg-accent animate-bounce" />
              <span className="ml-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                {t("advisorThinking")}
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-5 backdrop-blur-md" role="alert">
            <p className="font-semibold text-rose-400">{error.title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{error.message}</p>
            {lastSubmitted && (
              <button type="button" className="button-secondary mt-4 border-rose-500/30 hover:border-rose-500/50" onClick={() => void send(lastSubmitted, false)} disabled={isLoading}>
                <RefreshCw size={15} aria-hidden="true" />
                Retry message
              </button>
            )}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={submit} className="border-t border-white/10 bg-[#13152c]/90 p-4 backdrop-blur-xl">
        {selectedFile && (
          <div className="mb-3 flex items-center justify-between rounded-xl border border-orange-500/30 bg-orange-500/10 px-3 py-2 text-xs font-semibold text-white">
            <div className="flex items-center gap-2">
              <Paperclip size={14} className="text-accent" />
              <span>{selectedFile.name}</span>
              <span className="text-slate-400">({Math.round(selectedFile.size / 1024)} KB)</span>
            </div>
            <button
              type="button"
              className="text-slate-400 hover:text-rose-400"
              onClick={() => {
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
              title="Remove attachment"
            >
              <X size={14} aria-hidden="true" />
            </button>
          </div>
        )}

        <label className="field-label" htmlFor={`chat-input-${activeMode}`}>
          {activeMode === "rag" ? t("questionLabel") : t("messageToAgent")}
        </label>
        <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
          <textarea
            id={`chat-input-${activeMode}`}
            className="field min-h-24 resize-y bg-white/[0.04] text-white placeholder:text-slate-500"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={
              activeMode === "rag"
                ? t("chatRagPlaceholder")
                : t("chatAgentPlaceholder")
            }
            maxLength={2000}
          />
          <div className="flex items-center gap-2 sm:flex-col sm:items-stretch">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.doc,.docx"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) setSelectedFile(file);
              }}
            />
            <button
              type="button"
              className="button-secondary min-h-11 sm:min-h-11"
              onClick={() => fileInputRef.current?.click()}
              title="Attach document PDF"
            >
              <Paperclip size={18} aria-hidden="true" />
              <span className="hidden sm:inline">{t("attach")}</span>
            </button>
            <button
              type="submit"
              className="button-primary min-h-11 sm:min-h-12 sm:w-28"
              disabled={(!input.trim() && !selectedFile) || isLoading}
            >
              <ArrowUp size={18} aria-hidden="true" />
              {isLoading ? t("sending") : t("send")}
            </button>
          </div>
        </div>
        <div className="mt-2 flex items-center justify-between gap-3 text-xs text-muted">
          <span>{activeMode === "rag" ? t("noWebKnowledgeNotice") : t("chatAgentPlaceholder")}</span>
          <span>{input.length}/2000</span>
        </div>
      </form>
    </section>
  );
}
