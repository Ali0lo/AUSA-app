# AUSA frontend

This folder is the complete Next.js frontend for the current AUSA repository. It is intentionally scoped to capabilities that already have code-level support: student authentication, prototype programme matching, document-grounded questions, and the demonstration application agent.

The interface does not convert unavailable backend work into decorative controls. A user action either changes local state, navigates to a real route, calls an existing endpoint, or displays a specific unavailable or error state.

## Deployment configuration

The Azerbaijan DİM predictor is available at `/azerbaijan` and calls
`GET /api/v1/azerbaijan/predictions`. In a hosted frontend, set the server-side
`AUSA_API_URL` to the public FastAPI base URL, for example
`https://ausa-backend.example.com/api/v1`. Browser requests use the same-origin
Next.js proxy, so visitors do not need a direct API URL. Do not leave the example
`localhost` value in a hosted deployment: it means the frontend server itself,
not the visitor's intended backend.

## Status and scope

| Area | Route | Current status | Source of truth |
| --- | --- | --- | --- |
| Landing page | `/` | Available | Frontend content and the three original demo programme records |
| Student registration | `/register` | Backend-dependent | `POST /auth/register` |
| Student sign-in | `/sign-in` | Backend-dependent | `POST /auth/login`, `GET /auth/me`, and NextAuth |
| Programme matching | `/match` | Prototype | `POST /matching/evaluate` |
| AI document advisor | `/advisor` | Experimental | `POST /chat/ask` |
| Azerbaijan DİM cutoff predictor | `/azerbaijan` | Backend-dependent | `GET /azerbaijan/predictions` |
| Application assistant | `/application` | Demonstration | `GET /chat/agent/state` and `POST /chat/agent` |
| Earlier dashboard URL | `/dashboard` | Compatibility redirect | Opens `/match` |

The current limitations are visible inside the relevant screen:

- The catalogue contains the same three demo programmes used by the earlier frontend and seed script. The backend does not expose a programme-list endpoint.
- The match percentage is the existing rule-based prototype result. It is not presented as an admission probability.
- The repository may have no populated RAG document index. The advisor never invents a frontend answer when retrieval fails.
- The application agent and its tools currently return demonstration records. Checklist changes remain local and application submission is not offered.
- No social profile links were provided by the project. The footer does not display dead social icons.

## Design system

The visual direction is academic, restrained, and professional.

### Typography

- IBM Plex Serif is used for headings and high-emphasis figures.
- IBM Plex Sans is used for forms, navigation, labels, and body copy.
- Both families are installed as local npm assets, so the interface does not depend on a font CDN.

The serif has the seriousness of a traditional academic typeface without making the page resemble a newspaper. The sans-serif keeps long explanations and forms readable.

### Colour

| Token | Value | Use |
| --- | --- | --- |
| Canvas | `#F4F1EA` | Warm page background |
| Paper | `#FFFDFC` | Panels and input surfaces |
| Ink | `#1F211E` | Main text and dark surfaces |
| Muted | `#5F625D` | Secondary text |
| Line | `#8C8A82` | Strong borders |
| Quiet | `#D6D1C7` | Dividers and subtle borders |
| Accent | `#A64F27` | Burnt-orange actions and emphasis |
| Success | `#3F6B55` | Confirmed or ready states |
| Warning | `#9A6A20` | Experimental and caution states |
| Danger | `#A13D32` | Errors and missing requirements |

There are no purple, neon, or gradient palettes. Colour always has a functional role and is reinforced with text.

### Shape and layout

- Buttons, inputs, notices, tags, cards, and panels have square edges.
- Borders and spacing establish hierarchy instead of decorative shadows or floating cards.
- The maximum content width is 76 rem with responsive side padding.
- Desktop layouts collapse into single-column flows without hiding core content.
- The landing hero uses a locally stored university-library photograph with a solid dark overlay.

### Interaction and accessibility

- Every interactive element is a native link, button, input, select, or textarea.
- Focus states use a visible three-pixel accent outline.
- Forms have associated labels, constraints, autocomplete hints, and submit states.
- Dynamic success and failure messages use status or alert semantics.
- The page includes a keyboard skip link and labelled navigation regions.
- The mobile menu exposes its expanded state and closes after navigation.
- Reduced-motion preferences disable smooth scrolling and transitions.
- Source links open only when the backend returns an absolute HTTP or HTTPS URL.

## Project structure

```text
frontend
├── e2e
│   └── ausa.spec.ts
├── public
│   └── ausa-library-hero.jpg
├── scripts
│   └── normalize-next-env.mjs
├── src
│   ├── app
│   │   ├── advisor
│   │   ├── api/auth/[...nextauth]
│   │   ├── application
│   │   ├── dashboard
│   │   ├── match
│   │   ├── register
│   │   ├── sign-in
│   │   ├── error.tsx
│   │   ├── global-error.tsx
│   │   ├── layout.tsx
│   │   ├── loading.tsx
│   │   ├── not-found.tsx
│   │   └── page.tsx
│   ├── components
│   ├── lib
│   ├── test
│   └── types
├── .env.example
├── eslint.config.mjs
├── next.config.mjs
├── package.json
├── playwright.config.ts
├── postcss.config.js
├── run.bat
├── tailwind.config.js
├── tsconfig.json
└── vitest.config.ts
```

`src/app` owns routes and route-level composition. `src/components` owns reusable interactive surfaces. `src/lib/api.ts` is the only browser API compatibility layer. `src/lib/demo-programs.ts` contains the preserved demo catalogue. `src/types` mirrors current request and response contracts. Tests live beside the units they exercise, while complete browser flows live in `e2e`.

The source intentionally contains no explanatory code comments. This document holds the implementation and design guidance so behavior is described in one maintained place.

## Route behavior

### Landing page

The header links only to matching, the AI advisor, the application assistant, sign-in, and registration. The hero search covers programme name, university, field, country, and degree level for the three demo records.

Search outcomes are explicit:

- An empty query asks for a search value.
- One match opens that programme in `/match?program=<id>`.
- Several matches produce working links.
- No match states that the full catalogue is not implemented.

The rest of the page describes current capabilities, the real three-step matching flow, the frontend transparency policy, and the project team. It does not contain fabricated achievements, testimonials, statistics, or external profiles.

### Registration and sign-in

Registration sends the exact backend fields: email, password, GPA, budget, IELTS, TOEFL, degree level, field of study, and country. Password confirmation is checked before any network request. A successful registration starts a NextAuth credentials sign-in. If account creation succeeds but session creation fails, the page identifies that partial success and provides a sign-in link.

Sign-in uses the credentials provider in `src/app/api/auth/[...nextauth]/route.ts`:

1. The server posts email and password to `/auth/login`.
2. It requires an `access_token` in the response.
3. It requests `/auth/me` with that bearer token.
4. It validates that the profile includes an ID and email.
5. The token and profile are stored in the encrypted NextAuth JWT session.

The session token is used when the current backend endpoint supports bearer authentication. No secret or token is hard-coded into the repository.

### Matching

Guests use a complete manual profile form. A signed-in user has the form populated from `/auth/me`; if profile loading fails, the manual form remains usable and the failure is shown.

The selected student and programme are sent without changing the established envelope:

```json
{
  "student": {},
  "program": {}
}
```

The result screen requires the complete current response contract before rendering. It displays overall percentage, eligibility, ineligibility reasons, academic score, budget score, language score, degree-level score, weights, hard-filter states, and backend explanations. A malformed success response is reported as an unexpected backend response instead of causing a partial result or page crash.

### AI advisor

The advisor posts this established shape to `/chat/ask`:

```json
{
  "question": "Student question",
  "top_k": 5
}
```

It displays the returned answer and every returned source snippet, page, and safe source URL. The browser frontend does not call a general web search and does not create fallback advice if the request fails. Failed messages remain visible and can be retried without duplicating the user message.

### Application assistant

The page loads the current demonstration state with `student_id=std_demo` and `target_program_id=prog_101`. It presents the returned stage, missing documents, and motivation-letter draft.

Checklist buttons update local state and can always be reversed. Reload replaces local state with the backend state. Reset returns to the clearly labelled local demonstration. The copy button confirms clipboard success or gives a manual-copy instruction on failure.

Agent messages use the established shape:

```json
{
  "message": "Student message",
  "student_id": "std_demo",
  "target_program_id": "prog_101"
}
```

Returned stage, missing-document list, response text, and draft update the corresponding visible regions.

## API compatibility

The browser base URL comes from `NEXT_PUBLIC_API_URL`. Server-side authentication prefers `AUSA_API_URL`, allowing a deployment to use an internal backend address while browsers use a public address.

| Function | Method and path | Visible consumer |
| --- | --- | --- |
| Health | `GET /health` | Status badge and recheck button |
| Register | `POST /auth/register` | Registration form |
| Login | `POST /auth/login` | NextAuth credentials provider |
| Current profile | `GET /auth/me` | Session creation and matching profile |
| Match | `POST /matching/evaluate` | Matching form and result |
| RAG question | `POST /chat/ask` | AI advisor |
| Agent state | `GET /chat/agent/state` | Application page load and reload |
| Agent message | `POST /chat/agent` | Application chat and state update |

Requests have a 12-second browser timeout. Success payloads are structurally checked before a feature consumes them.

## Failure model

| Condition | Visible heading | Behavior |
| --- | --- | --- |
| Network connection fails | Backend unavailable | Names the disabled feature and keeps unrelated local UI usable |
| Request exceeds 12 seconds | Request timed out | Gives the timeout duration and retry guidance |
| Backend returns 401 | Authentication required | Identifies a rejected or expired session |
| Backend returns 404 or 501 | Feature unavailable | States that the connected backend does not implement the feature |
| Backend returns 422 | Invalid request | Preserves field-level validation detail returned by FastAPI |
| Other non-success response | Backend error | Shows the backend detail or HTTP status |
| Success body does not match the contract | Unexpected backend response | Prevents unsafe partial rendering |
| Unexpected render exception | Interface error | Provides retry and home actions |
| Unknown route | 404 · Page not found | Provides working home and matching links |

No request failure is replaced by demo data. Demo data is used only where it already existed in the earlier frontend or backend demonstration and is labelled before interaction.

## Environment

Create `.env.local` from `.env.example`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
AUSA_API_URL=http://localhost:8000/api/v1
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=replace-with-a-long-random-secret
```

`NEXTAUTH_SECRET` must be a long, unpredictable value. A local value can be generated with:

```bash
openssl rand -base64 32
```

For production, set `NEXTAUTH_URL` to the public frontend origin, use a deployment secret manager, expose the correct public API URL, and include the frontend origin in the backend CORS configuration.

## Run locally

Requirements:

- Node.js 20.19 or later
- npm 9 or later
- An AUSA backend at the configured API URL for backend-dependent features

From this folder:

```bash
npm install
cp .env.example .env.local
npm run dev
```

Update `NEXTAUTH_SECRET` in `.env.local`, then open `http://localhost:3000`.

On Windows, `run.bat` is included inside the frontend folder. Double-click it or run it from Command Prompt:

```cmd
run.bat
```

The Windows launcher installs the locked dependencies, creates `.env.local` when it is missing, generates the local authentication secret, clears the disposable Next.js cache, and starts the development server.

The interface still loads when the backend is offline. Status badges and feature-level messages will identify which operations cannot run.

## Run the existing backend

From the repository root, start PostgreSQL:

```bash
docker compose up -d postgres
```

In another terminal:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_db.py
uvicorn app.main:app --reload --port 8000
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

The seed script creates the current database tables and demonstration records. Its development account is `student@ausa.az` with password `password123`. This account is for local demonstration only.

Check the backend at `http://localhost:8000/api/v1/health` before exercising authenticated features.

## Production build

```bash
npm install
npm run build
npm run start
```

The build runs type checking and creates an optimized Next.js application. The post-build normalization script keeps the generated Next.js declaration file free of generated comments, matching this frontend's source policy.

## Verification

Install the Playwright browser once:

```bash
npx playwright install chromium
```

Available checks:

```bash
npm run lint
npm run test
npm run build
npm run test:e2e
npm run check
```

`npm run test` covers catalogue search, request envelopes, response validation, detailed errors, safe source URLs, matching result presentation, document toggles, status rechecks, and chat retry behavior.

`npm run test:e2e` starts an isolated frontend and mocks the incomplete backend at the network boundary. It covers landing search outcomes, desktop and mobile navigation, health rechecks, matching success and failure, retry and reset, advisor sources and recovery, every local application action, clipboard behavior, agent updates, registration validation and success, sign-in rejection and success, the dashboard compatibility redirect, and the not-found exits.

## Team-safe extension rules

1. Add a visible capability only after a route, endpoint, or complete local interaction exists.
2. Keep request and response translation inside `src/lib/api.ts`.
3. Extend the shared types before consuming new backend fields.
4. Preserve existing endpoint paths and payload envelopes unless the backend contract changes with the frontend.
5. Add an explicit loading, empty, success, unavailable, and failure state for every new request.
6. Never silently fall back from a failed backend request to demo data.
7. Keep demo data centralized and labelled.
8. Add unit coverage for response validation and browser coverage for the complete user action.
9. Keep implementation guidance in this document instead of adding code comments.
10. Run `npm run check` before handing the folder to another team member.

## Image credit

The locally stored hero photograph is by Ilia Bronskiy on Unsplash. The source page is linked from the site footer: `https://unsplash.com/photos/a-library-filled-with-lots-of-books-and-people-sitting-at-tables-gdZ9GPNi_VM`.
