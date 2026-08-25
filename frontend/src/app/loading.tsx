export default function Loading() {
  return (
    <div className="app-page" role="status" aria-live="polite">
      <div className="panel mx-auto max-w-3xl p-8">
        <p className="eyebrow">Loading</p>
        <p className="mt-3 font-serif text-2xl font-semibold">Preparing the requested page.</p>
      </div>
    </div>
  );
}
