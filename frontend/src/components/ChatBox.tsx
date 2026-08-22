"use client";

import React, { useEffect, useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api";
import { ChatMessage } from "@/types";

interface ChatBoxProps {
  studentId?: string;
  programId?: string;
}

export const ChatBox: React.FC<ChatBoxProps> = ({
  studentId = "std_demo",
  programId = "prog_demo",
}) => {
  const [mode, setMode] = useState<"rag" | "agent">("rag");
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome-1",
      role: "assistant",
      content:
        "Salam! I am your AUSA AI Advisor. You can ask me general questions about university guidelines and scholarships, or switch to Application Guide mode for step-by-step application assistance.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userText = inputMessage.trim();
    setInputMessage("");

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(userText, mode, studentId, programId);

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        sources: response.sources,
        application_stage: response.applicationStage,
        missing_documents: response.missingDocs,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error: any) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `Sorry, an error occurred: ${error.message || "Unable to reach backend service."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full flex flex-col h-[600px] rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden backdrop-blur-md">
      {/* Top Header & Mode Toggle Bar */}
      <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
          <h3 className="font-bold text-white text-base">AUSA AI Advisor</h3>
        </div>

        {/* Dual Mode Toggle Buttons */}
        <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setMode("rag")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mode === "rag"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            🔍 General Q&A (RAG)
          </button>
          <button
            type="button"
            onClick={() => setMode("agent")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mode === "agent"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            🤖 Application Guide (Agent)
          </button>
        </div>
      </div>

      {/* Mode Sub-banner Info */}
      <div className="px-4 py-2 bg-slate-900/60 border-b border-slate-800/80 text-xs text-slate-400 flex items-center justify-between">
        <span>
          {mode === "rag"
            ? "Mode: Strictly grounded document guidelines search (PostgreSQL pgvector RAG)."
            : "Mode: Stateful application dossier advisor & motivation letter drafting tool."}
        </span>
      </div>

      {/* Message History Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-950/40">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-blue-600 text-white rounded-br-none shadow-lg shadow-blue-600/20"
                  : "bg-slate-800 text-slate-100 rounded-bl-none border border-slate-700/60 shadow-md"
              }`}
            >
              {/* Message Content */}
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* RAG Sources Section */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t border-slate-700/80 text-xs space-y-1">
                  <div className="font-semibold text-blue-300 flex items-center gap-1">
                    <span>📚 Referenced Sources ({msg.sources.length}):</span>
                  </div>
                  <div className="space-y-1 text-slate-300">
                    {msg.sources.map((src, i) => (
                      <div
                        key={i}
                        className="bg-slate-900/60 p-2 rounded-md border border-slate-700/50"
                      >
                        <p className="italic font-mono text-[11px] text-slate-300">
                          "{src.content_snippet}"
                        </p>
                        {src.source_url && (
                          <a
                            href={src.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-400 hover:underline text-[10px] block mt-1"
                          >
                            🔗 Source Link
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Agent Application Stage & Missing Documents Checklist */}
              {msg.missing_documents && msg.missing_documents.length > 0 && (
                <div className="mt-3 pt-2 border-t border-slate-700/80 text-xs space-y-1 text-amber-300">
                  <div className="font-semibold">📋 Missing Dossier Documents:</div>
                  <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                    {msg.missing_documents.map((doc, idx) => (
                      <li key={idx} className="font-mono text-xs">
                        {doc}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <span className="text-[10px] text-slate-500 px-1 mt-1 font-mono">
              {msg.timestamp}
            </span>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start gap-2">
            <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-bl-none px-4 py-3 text-sm text-slate-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" />
              <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce delay-150" />
              <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce delay-300" />
              <span className="text-xs">
                {mode === "rag" ? "Searching guidelines vector DB..." : "Agent processing workflow..."}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form
        onSubmit={handleSendMessage}
        className="p-3 bg-slate-900 border-t border-slate-800 flex items-center gap-2"
      >
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder={
            mode === "rag"
              ? "Ask a question (e.g. 'What is the IELTS requirement for DAAD scholarship?')..."
              : "Ask the application guide (e.g. 'Draft my motivation letter')..."
          }
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
        />

        <button
          type="submit"
          disabled={!inputMessage.trim() || isLoading}
          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-blue-600/30"
        >
          Send
        </button>
      </form>
    </div>
  );
};
