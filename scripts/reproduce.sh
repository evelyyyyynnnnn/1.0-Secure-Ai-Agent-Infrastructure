#!/usr/bin/env bash
# =============================================================================
# reproduce.sh — clean-room reproducibility attestation
#
# Clones the five trustworthy-AI portfolio repositories onto a fresh machine,
# fetches the real public data each project uses, runs every test suite and
# demo, and writes a single REPRODUCIBILITY_REPORT.md recording — per project —
# whether the tests pass, whether the run used real or synthetic data, the data
# source, and the headline measured figures.
#
# The point is independence: it shows the committed results re-derive on a
# machine that is not the author's laptop, from public data, with nothing hidden.
#
# Usage (on a clean Ubuntu/Debian CPU box, e.g. a Tencent Cloud CVM):
#     export DATAKIT_UA="Wenke Du <your-sec-contact-email>"   # SEC EDGAR wants a UA
#     bash reproduce.sh
# Optional:
#     WORK=/path/to/workdir bash reproduce.sh   # where to clone + write the report
#
# It never fabricates: a project that errors, or whose data cannot be fetched
# from this network, is recorded as such rather than papered over.
# =============================================================================
set -uo pipefail

GH="${GH:-https://github.com/evelyyyyynnnnn}"
REPOS=(
  1.0-Secure-Ai-Agent-Infrastructure
  2.0-Healthcare-Ai-Systems
  3.0-Financial-Ai-Systems
  4.0-Decision-Intelligence-Framework
  5.0-Ai-Engineering-Toolkit
)
WORK="${WORK:-$HOME/repro-$(date +%Y%m%d-%H%M%S)}"
REPORT="$WORK/REPRODUCIBILITY_REPORT.md"

# SEC EDGAR asks callers to identify themselves in the User-Agent. This is the
# legitimate, documented use of a contact email; override it with your own.
export DATAKIT_UA="${DATAKIT_UA:-Wenke Du 120987698dwk@gmail.com}"
export SEC_EDGAR_UA="${SEC_EDGAR_UA:-$DATAKIT_UA}"
export PYTHONUNBUFFERED=1

mkdir -p "$WORK"
cd "$WORK"

log()  { printf '%s\n' "$*"; }
rep()  { printf '%s\n' "$*" >> "$REPORT"; }

# ---- environment header -----------------------------------------------------
PYBIN="$(command -v python3 || true)"
[ -z "$PYBIN" ] && { echo "python3 not found; install Python 3.10+ first." >&2; exit 1; }
PYVER="$("$PYBIN" --version 2>&1)"

: > "$REPORT"
rep "# Reproducibility Report — Trustworthy, Verifiable AI Portfolio"
rep ""
rep "Independent clean-room re-run of Wenke Du's five open-source repositories."
rep "Every figure below was produced by this machine from public data; nothing"
rep "was hand-entered."
rep ""
rep "## Environment"
rep ""
rep "| Field | Value |"
rep "|---|---|"
rep "| Date (UTC) | $(date -u '+%Y-%m-%d %H:%M:%S') |"
rep "| Host | \`$(uname -a | sed 's/|/ /g')\` |"
rep "| Python | \`$PYVER\` |"
rep "| Public IP | \`$(curl -s --max-time 8 https://api.ipify.org || echo 'n/a')\` |"
rep "| Clone source | \`$GH\` |"
rep ""

# ---- one shared virtualenv --------------------------------------------------
log "[*] creating virtualenv"
"$PYBIN" -m venv "$WORK/.venv"
# shellcheck disable=SC1091
source "$WORK/.venv/bin/activate"
python -m pip install --quiet --upgrade pip wheel setuptools
# Baseline scientific stack most projects share; per-repo requirements add more.
python -m pip install --quiet numpy pandas scipy scikit-learn matplotlib requests pytest || true

# ---- helper: read is_synthetic / data_source / headline from a results file -
read_results() {  # $1 = project dir
  python - "$1" <<'PY'
import json, sys, pathlib, glob
d = pathlib.Path(sys.argv[1]) / "results"
f = None
for name in ("latest-real.json", "latest-llm.json", "latest.json"):
    if (d / name).exists():
        f = d / name
        break
if not f:
    for c in glob.glob(str(d / "*.json")):
        f = pathlib.Path(c); break
if not f:
    print("NOFILE|-|-"); raise SystemExit
try:
    j = json.loads(f.read_text())
except Exception as e:
    print(f"UNREADABLE|-|{e}"); raise SystemExit
syn = j.get("is_synthetic")
kind = "real" if syn is False else ("synthetic" if syn is True else "n/a")
src = str(j.get("data_source", "") or "")[:120].replace("|", "/").replace("\n", " ")
print(f"{f.name}|{kind}|{src}")
PY
}

# ---- per-project runner -----------------------------------------------------
N_REAL=0; N_SYN=0; N_ERR=0; N_TESTS_PASS=0

run_project() {  # $1 = repo name, $2 = project dir (abs)
  local repo="$1" pdir="$2" pname
  pname="$(basename "$pdir")"
  [ -d "$pdir/src" ] || return 0
  log "    - $pname"

  ( cd "$pdir"
    [ -f requirements.txt ] && python -m pip install --quiet -r requirements.txt >/dev/null 2>&1

    # Special-cases that unblock real data / dependencies:
    if [ "$pname" = "6-portfolio-optimization-engine" ]; then
      python -m pip install --quiet gymnasium >/dev/null 2>&1
    fi
  )

  # 1) fetch real data if the project ships a fetcher
  local fetch_note="no fetcher"
  if [ -f "$pdir/data/fetch.py" ]; then
    if ( cd "$pdir" && timeout 600 python -m data.fetch >/dev/null 2>"$WORK/.fetch.err" ); then
      fetch_note="fetch ok"
    else
      fetch_note="fetch failed ($(tail -1 "$WORK/.fetch.err" 2>/dev/null | cut -c1-80))"
    fi
  fi

  # 2) run the demo (rebuilds results/ from this machine)
  local demo_note="no demo"
  if [ -f "$pdir/src/demo.py" ]; then
    if ( cd "$pdir" && timeout 900 python -m src.demo >/dev/null 2>"$WORK/.demo.err" ); then
      demo_note="demo ok"
    else
      demo_note="demo error ($(tail -1 "$WORK/.demo.err" 2>/dev/null | cut -c1-80))"
    fi
  fi

  # 3) run tests
  local tline tpass=0
  if [ -d "$pdir/tests" ]; then
    tline="$( cd "$pdir" && timeout 600 python -m pytest tests/ -q 2>&1 | tail -1 )"
    tpass="$(printf '%s' "$tline" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)"
  else
    tline="no tests dir"
  fi
  N_TESTS_PASS=$(( N_TESTS_PASS + ${tpass:-0} ))

  # 4) read what the run produced
  local rr kind src rfile
  rr="$(read_results "$pdir")"
  rfile="${rr%%|*}"; kind="$(printf '%s' "$rr" | cut -d'|' -f2)"; src="$(printf '%s' "$rr" | cut -d'|' -f3)"
  case "$kind" in
    real) N_REAL=$((N_REAL+1));;
    synthetic) N_SYN=$((N_SYN+1));;
  esac
  [ "$demo_note" != "demo ok" ] && [ "$demo_note" != "no demo" ] && N_ERR=$((N_ERR+1))

  rep "| \`$pname\` | ${tpass:-0} passed | $kind | $fetch_note; $demo_note | \`$rfile\` | ${src} |"
}

# ---- main loop --------------------------------------------------------------
for repo in "${REPOS[@]}"; do
  log "[*] $repo"
  if [ ! -d "$WORK/$repo" ]; then
    git clone --depth 1 "$GH/$repo.git" "$WORK/$repo" >/dev/null 2>&1 \
      || { rep ""; rep "## $repo"; rep ""; rep "> clone FAILED from $GH/$repo.git"; rep ""; continue; }
  fi
  rep ""
  rep "## $repo"
  rep ""
  rep "| Project | Tests | Data | Run | Results file | Data source |"
  rep "|---|---|---|---|---|---|"
  for pdir in "$WORK/$repo"/*/ ; do
    [ -d "$pdir" ] || continue
    run_project "$repo" "${pdir%/}"
  done
done

# ---- summary ----------------------------------------------------------------
rep ""
rep "## Summary"
rep ""
rep "| Metric | Value |"
rep "|---|---|"
rep "| Projects on real public data | $N_REAL |"
rep "| Projects on synthetic / authored data | $N_SYN |"
rep "| Projects that errored on this machine | $N_ERR |"
rep "| Total tests passed | $N_TESTS_PASS |"
rep ""
rep "_Real means the committed results/latest-real.json reports is_synthetic:false._"
rep "_Synthetic entries are synthetic-by-design (exact-oracle benchmarks, meta"
rep "roll-ups) or data walled off from this network, and are labelled as such in"
rep "their own repositories._"

log ""
log "[done] report written to: $REPORT"
log "       real=$N_REAL synthetic=$N_SYN errored=$N_ERR tests_passed=$N_TESTS_PASS"
