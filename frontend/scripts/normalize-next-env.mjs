import { existsSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";

const content = [
  'import "next";',
  'import "next/image-types/global";',
  ""
].join("\n");

writeFileSync(new URL("../next-env.d.ts", import.meta.url), content);

const agentsFile = new URL("../AGENTS.md", import.meta.url);
const claudeFile = new URL("../CLAUDE.md", import.meta.url);

if (existsSync(agentsFile)) {
  const agentsContent = readFileSync(agentsFile, "utf8").trim();
  if (agentsContent.startsWith("<!-- BEGIN:nextjs-agent-rules -->") && agentsContent.endsWith("<!-- END:nextjs-agent-rules -->")) {
    unlinkSync(agentsFile);
  }
}

if (existsSync(claudeFile) && readFileSync(claudeFile, "utf8").trim() === "@AGENTS.md") {
  unlinkSync(claudeFile);
}
