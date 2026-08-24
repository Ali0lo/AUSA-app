import { ArrowLeft, Scale } from "lucide-react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="app-page">
      <div className="panel-strong mx-auto max-w-3xl p-8 sm:p-12">
        <p className="eyebrow">404 · Page not found</p>
        <h1 className="page-heading mt-4">This route does not exist.</h1>
        <p className="body-large mt-5">The link may be outdated. No hidden or unfinished page is available at this address.</p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link className="button-primary" href="/"><ArrowLeft size={17} aria-hidden="true" />Return home</Link>
          <Link className="button-secondary" href="/match"><Scale size={17} aria-hidden="true" />Open matching</Link>
        </div>
      </div>
    </div>
  );
}
