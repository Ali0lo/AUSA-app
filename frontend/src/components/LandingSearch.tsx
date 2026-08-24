"use client";

import { Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { DEMO_PROGRAMS, findDemoPrograms } from "@/lib/demo-programs";
import { ProgramRequirements } from "@/types";

export function LandingSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState<ProgramRequirements[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const results = findDemoPrograms(query);

    if (!query.trim()) {
      setMatches([]);
      setMessage("Enter a programme, university, field, or country to search the demo catalogue.");
      return;
    }

    if (results.length === 1) {
      router.push(`/match?program=${results[0].program_id}`);
      return;
    }

    setMatches(results);
    setMessage(
      results.length > 1
        ? `${results.length} demo programmes match your search.`
        : "No demo programme matches that search. The full catalogue is not implemented yet."
    );
  }

  return (
    <div className="w-full max-w-3xl">
      <form onSubmit={submit} className="grid border border-paper bg-paper sm:grid-cols-[1fr_auto]">
        <label className="sr-only" htmlFor="landing-program-search">Search the demo programme catalogue</label>
        <input
          id="landing-program-search"
          name="program-search"
          className="min-h-14 min-w-0 border-0 bg-paper px-4 text-base text-ink placeholder:text-[#6f6d66] focus:outline-none"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setMessage(null);
            setMatches([]);
          }}
          placeholder="Search programme, university, field, or country"
          list="demo-program-options"
        />
        <datalist id="demo-program-options">
          {DEMO_PROGRAMS.map((program) => (
            <option key={program.program_id} value={program.program_name}>{program.university_name}</option>
          ))}
        </datalist>
        <button type="submit" className="button-primary min-h-14 border-0 border-t border-accent sm:border-l sm:border-t-0">
          <Search size={18} aria-hidden="true" />
          Search demo
        </button>
      </form>

      <div className="mt-3 min-h-6 text-sm text-paper" role="status" aria-live="polite">
        {message && <p>{message}</p>}
        {matches.length > 1 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {matches.map((program) => (
              <Link
                key={program.program_id}
                href={`/match?program=${program.program_id}`}
                className="border border-paper bg-[#1f211ee6] px-3 py-2 font-semibold hover:bg-paper hover:text-ink"
              >
                {program.program_name}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
