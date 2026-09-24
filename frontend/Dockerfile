# ==========================================
# Next.js frontend, built to a standalone server.
#
# The browser never calls the API directly: next.config.mjs rewrites /api/v1/* to
# AUSA_API_URL server-side, so there is one origin and no CORS to configure.
#
# AUSA_API_URL is a BUILD argument, not a runtime variable. Next resolves rewrites()
# when it builds and serializes them into .next; setting the variable only on the
# running container has no effect. Rebuild the image to point at a different backend.
# ==========================================

FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-slim AS builder
WORKDIR /app
ARG AUSA_API_URL=http://api:8000/api/v1
ENV AUSA_API_URL=$AUSA_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Run as the image's own unprivileged user rather than root.
USER node

# standalone carries server.js and the minimal node_modules; static and public are
# not traced into it and have to be copied beside it.
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
