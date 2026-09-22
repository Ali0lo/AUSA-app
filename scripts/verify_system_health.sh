#!/usr/bin/env bash
# ==============================================================================
# AUSA Full-System Health & Test Verification Runner
# Authors: Ali0lo <aliaze975@gmail.com>
# ==============================================================================

set -euo pipefail

CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          AUSA PLATFORM SYSTEM VERIFICATION RUNNER             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# 1. Environment & CLI Smoke Test
echo -e "${YELLOW}[1/4] Verifying Python virtual environment and AUSA CLI...${RESET}"
if [ ! -f ".venv/bin/python" ]; then
    echo -e "${RED}Error: .venv/bin/python not found.${RESET}"
    exit 1
fi

./bin/ausa --version
./bin/ausa convert --amount 1000 --from EUR --to AZN > /dev/null
echo -e "${GREEN}✓ CLI and Virtualenv operational.${RESET}\n"

# 2. Backend Pytest Suite
echo -e "${YELLOW}[2/4] Running Backend Pytest suite (490+ tests)...${RESET}"
(
    cd backend
    PYTHONPATH=. ../.venv/bin/pytest -q --tb=short
)
echo -e "${GREEN}✓ Backend Pytest suite 100% passing.${RESET}\n"

# 3. Frontend Vitest Suite
echo -e "${YELLOW}[3/4] Running Frontend Vitest suite (120+ tests)...${RESET}"
(
    cd frontend
    npm run test
)
echo -e "${GREEN}✓ Frontend Vitest suite 100% passing.${RESET}\n"

# 4. Summary Verdict
echo -e "${GREEN}${BOLD}"
echo "================================================================="
echo "  ALL CHECKS PASSED: 620+ automated tests verified (100% green)"
echo "  AUSA Platform is production-ready."
echo "================================================================="
echo -e "${RESET}"

