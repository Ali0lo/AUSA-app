"use client";

import { ArrowLeft, Route } from "lucide-react";
import Link from "next/link";
import { useLanguage } from "@/lib/i18n";

export default function NotFound() {
  const { t } = useLanguage();

  return (
    <div className="app-page">
      <div className="panel-strong mx-auto max-w-3xl p-8 sm:p-12">
        <p className="eyebrow">404 · {t("pageNotFound", "Page not found")}</p>
        <h1 className="page-heading mt-4">{t("routeNotExist", "This route does not exist.")}</h1>
        <p className="body-large mt-5">
          {t("notFoundHelp", "The link may be outdated. No hidden or unfinished page is available at this address.")}
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link className="button-primary" href="/">
            <ArrowLeft size={17} aria-hidden="true" />
            {t("returnHome", "Return home")}
          </Link>
          <Link className="button-secondary" href="/plan">
            <Route size={17} aria-hidden="true" />
            {t("plan")}
          </Link>
        </div>
      </div>
    </div>
  );
}
