"use client";

export default function RootError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body className="bg-canvas p-6 font-sans text-ink">
        <main className="mx-auto mt-16 max-w-3xl border border-line border-l-4 border-l-danger bg-paper p-8" role="alert">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Application error</p>
          <h1 className="mt-4 font-serif text-4xl font-semibold">AUSA could not load the page shell.</h1>
          <p className="mt-5 leading-7 text-muted">Retry the interface. If the error continues, restart the frontend and review its terminal output.</p>
          <button type="button" className="mt-7 min-h-11 border border-accent bg-accent px-5 py-2.5 font-semibold text-paper" onClick={reset}>Retry application</button>
        </main>
      </body>
    </html>
  );
}
