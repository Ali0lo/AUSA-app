import { Check } from "lucide-react";

export type ApplicationStage = "gathering_info" | "drafting_documents" | "ready_to_submit";

const steps: Array<{ id: ApplicationStage; label: string; description: string }> = [
  { id: "gathering_info", label: "Gather information", description: "Review the required dossier records" },
  { id: "drafting_documents", label: "Draft documents", description: "Prepare the motivation-letter demonstration" },
  { id: "ready_to_submit", label: "Ready for review", description: "All locally tracked documents are marked ready" }
];

export function ApplicationStepper({ currentStage }: { currentStage: ApplicationStage | string }) {
  const order: Record<string, number> = {
    gathering_info: 0,
    drafting_documents: 1,
    ready_to_submit: 2
  };
  const current = order[currentStage] ?? 0;

  return (
    <section className="panel-strong p-6 sm:p-8" aria-labelledby="application-progress-heading">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-5">
        <div>
          <h2 id="application-progress-heading" className="font-serif text-2xl font-semibold">Application progress</h2>
          <p className="mt-1 text-sm text-muted">This state is a frontend demonstration and is not persisted.</p>
        </div>
        <span className="status-tag status-demo">{currentStage.replace(/_/g, " ")}</span>
      </div>
      <ol className="mt-7 grid border-y border-quiet md:grid-cols-3">
        {steps.map((step, index) => {
          const complete = index < current;
          const active = index === current;
          return (
            <li key={step.id} className={`p-5 ${index > 0 ? "border-t border-quiet md:border-l md:border-t-0" : ""}`} aria-current={active ? "step" : undefined}>
              <div className={`flex h-9 w-9 items-center justify-center border text-sm font-semibold ${active ? "border-accent bg-accent text-paper" : complete ? "border-success bg-success text-paper" : "border-line text-muted"}`}>
                {complete ? <Check size={17} aria-label="Completed" /> : index + 1}
              </div>
              <h3 className="mt-5 font-serif text-xl font-semibold">{step.label}</h3>
              <p className="mt-2 text-sm leading-6 text-muted">{step.description}</p>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
