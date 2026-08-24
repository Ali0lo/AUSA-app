"use client";

import { useSession } from "next-auth/react";
import { ChatBox } from "@/components/ChatBox";
import { FeatureTag } from "@/components/FeatureTag";
import { Notice } from "@/components/Notice";
import { ServiceStatus } from "@/components/ServiceStatus";

export default function AdvisorPage() {
  const { data: session } = useSession();

  return (
    <div className="app-page">
      <div className="flex flex-col gap-6 border-b border-line pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-3">
            <p className="eyebrow">Document Q&A</p>
            <FeatureTag state="experimental" />
          </div>
          <h1 className="page-heading mt-4">Ask against the retrieved university documents.</h1>
          <p className="body-large mt-5">
            The advisor sends questions to the existing RAG endpoint and presents both the answer and every source object returned by the backend.
          </p>
        </div>
        <ServiceStatus />
      </div>

      <div className="mt-7">
        <Notice title="Evidence depends on backend data" tone="warning">
          The repository does not include a populated document index. An empty answer, an explicit “I do not have this information” response, or a backend error is a valid current state.
        </Notice>
      </div>

      <div className="mt-9 grid gap-8 lg:grid-cols-[0.72fr_1.28fr] lg:items-start">
        <aside className="panel-strong p-6 sm:p-8">
          <h2 className="font-serif text-2xl font-semibold">What this page verifies</h2>
          <ul className="mt-5 divide-y divide-quiet border-y border-quiet text-sm leading-6 text-muted">
            <li className="py-4">The question is submitted to <code className="font-mono text-xs text-ink">/chat/ask</code>.</li>
            <li className="py-4">Returned document snippets and source links remain attached to the answer.</li>
            <li className="py-4">Offline, timeout, authorization, and missing-endpoint failures are named explicitly.</li>
            <li className="py-4">The frontend does not manufacture an answer when the request fails.</li>
          </ul>
        </aside>
        <ChatBox lockedMode="rag" token={session?.user?.accessToken} />
      </div>
    </div>
  );
}
