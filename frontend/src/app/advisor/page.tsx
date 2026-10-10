"use client";

import { useSession } from "next-auth/react";
import { ChatBox } from "@/components/ChatBox";
import { FeatureTag } from "@/components/FeatureTag";
import { Notice } from "@/components/Notice";
import { ServiceStatus } from "@/components/ServiceStatus";
import { useLanguage } from "@/lib/i18n";

export default function AdvisorPage() {
  const { data: session } = useSession();
  const { t } = useLanguage();

  return (
    <div className="app-page">
      <div className="flex flex-col gap-6 border-b border-line pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-3">
            <p className="eyebrow">{t("advisorEyebrow")}</p>
            <FeatureTag state="experimental" />
          </div>
          <h1 className="page-heading mt-4">{t("advisorHeading")}</h1>
          <p className="body-large mt-5">
            {t("advisorBody")}
          </p>
        </div>
        <ServiceStatus />
      </div>

      <div className="mt-7">
        <Notice title={t("evidenceNoticeTitle")} tone="warning">
          {t("evidenceNoticeBody")}
        </Notice>
      </div>

      <div className="mt-9 grid gap-8 lg:grid-cols-[0.72fr_1.28fr] lg:items-start">
        <aside className="panel-strong p-6 sm:p-8">
          <h2 className="font-serif text-2xl font-semibold">{t("whatThisVerifies")}</h2>
          <ul className="mt-5 divide-y divide-quiet border-y border-quiet text-sm leading-6 text-muted">
            <li className="py-4">
              {t("verifies1")}{" "}
              <code className="font-mono text-xs text-ink">/chat/ask</code>.
            </li>
            <li className="py-4">
              {t("verifies2")}
            </li>
            <li className="py-4">
              {t("verifies3")}
            </li>
            <li className="py-4">
              {t("verifies4")}
            </li>
          </ul>
        </aside>
        <ChatBox lockedMode="rag" token={session?.user?.accessToken} />
      </div>
    </div>
  );
}
