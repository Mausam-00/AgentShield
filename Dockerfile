# AgentShield AI — container image bundling the Next.js site with the Python engine.
#
# Why a container: the website's /api/assess route shells out to the Python
# AgentShield engine (scripts/agentshield_report.py). Serverless Node hosts
# (e.g. Vercel) can't run that, and hosts that only deploy the web subfolder
# don't ship the engine. This image guarantees BOTH the Node server and Python 3
# (plus the whole repo) are present at runtime. The engine is pure stdlib, so no
# pip install is required.
#
# Build from the REPOSITORY ROOT (not from agentshield-web/):
#   docker build -t agentshield .
#   docker run -p 3000:3000 agentshield
# Then open http://localhost:3000 and use the "Assess your agent" section.

# ---- Stage 1: build the Next.js app ----
FROM node:20-bookworm-slim AS web-build
WORKDIR /app/agentshield-web
COPY agentshield-web/package*.json ./
RUN npm ci
COPY agentshield-web/ ./
RUN npm run build

# ---- Stage 2: runtime (Node server + Python 3 engine) ----
FROM node:20-bookworm-slim AS runtime
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 ca-certificates \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The Python engine, CLI scripts, and the HTML-report skill the route imports.
COPY agentshield/ ./agentshield/
COPY scripts/ ./scripts/
COPY .github/ ./.github/

# The built website (includes node_modules and .next needed by `next start`).
COPY --from=web-build /app/agentshield-web ./agentshield-web

ENV NODE_ENV=production
ENV AGENTSHIELD_PYTHON=python3
ENV PORT=3000
EXPOSE 3000

# `next start` runs with cwd = /app/agentshield-web, so the route resolves the
# repo root at /app and finds scripts/agentshield_report.py + agentshield/.
WORKDIR /app/agentshield-web
CMD ["npm", "run", "start"]
