# ==========================================
# Next.js frontend, built to a standalone server.
#
# The browser never calls the API directly: next.config.mjs rewrites /api/v1/* to
# AUSA_API_URL server-side, so there is one origin and no CORS to configure.
#
# AUSA_API_URL is needed in BOTH stages, for two different mechanisms:
#
#   - at build, because Next resolves rewrites() when it builds and serializes them
#     into .next; setting it only on the running container does not move the proxy.
#   - at run, because src/app/api/auth/[...nextauth]/route.ts reads it directly and
#     fetches /auth/login and /auth/me itself rather than going through the proxy.
#     A builder-stage ENV is discarded with the stage, so without it here that read
#     returns undefined and falls back to http://localhost:8000 -- which inside this
#     container is this container, and sign-in fails with ECONNREFUSED.
#
# Changing where the backend lives therefore means rebuilding, not just restarting.
# ==========================================
ARG AUSA_API_URL=http://api:8000/api/v1

FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-slim AS builder
WORKDIR /app
ARG AUSA_API_URL
ENV AUSA_API_URL=$AUSA_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ARG AUSA_API_URL
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
# For the NextAuth route's own fetches -- see the note at the top. Compose overrides it.
ENV AUSA_API_URL=$AUSA_API_URL

# Run as the image's own unprivileged user rather than root.
USER node

# standalone carries server.js and the minimal node_modules; static and public are
# not traced into it and have to be copied beside it.
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
