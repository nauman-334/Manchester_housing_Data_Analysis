#!/bin/bash
# ------------------------------------------------------------------
# One-click environment setup for Manchester_housing_Data_Analysis
#
# Double-click in Finder, or run:  bash setup_environment.command
# It (re)builds the virtual environment in ./venv with ONE Python,
# installs requirements.txt, registers a Jupyter kernel and runs the
# unit tests and the full pipeline to prove that everything works.
# Output is also saved to setup_log.txt.
# ------------------------------------------------------------------

# Run from the folder that contains this script (the project root).
cd "$(dirname "$0")" || exit 1
# Copy everything printed into setup_log.txt as well.
exec > >(tee setup_log.txt) 2>&1

finish() {
    echo ""
    read -r -p "Press Enter to close this window..." _
    exit "$1"
}

echo "Setup started: $(date)"
echo "Project folder: $(pwd)"

# ---- 1. Choose ONE Python (Miniconda first; never the uv-managed one) --
CANDIDATES=(
    "/opt/homebrew/Caskroom/miniconda/base/bin/python3"
    "$HOME/miniconda3/bin/python3"
    "/Library/Frameworks/Python.framework/Versions/Current/bin/python3"
    "/usr/local/bin/python3"
    "/opt/homebrew/bin/python3"
)
PY=""
for candidate in "${CANDIDATES[@]}"; do
    [ -x "$candidate" ] || continue
    if "$candidate" -c 'import sys, venv; sys.exit(sys.version_info < (3, 10))' \
        2>/dev/null; then
        PY="$candidate"
        break
    fi
done
if [ -z "$PY" ]; then
    echo "ERROR: no suitable Python 3.10+ found (Miniconda or python.org)."
    finish 1
fi
echo "[1/5] Using $("$PY" --version 2>&1) at $PY"

# ---- 2. Build or repair ./venv ---------------------------------------
VPY="venv/bin/python"
if "$VPY" -c 'import sys' 2>/dev/null; then
    echo "[2/5] venv works - reusing it."
else
    echo "[2/5] venv is missing or broken - rebuilding it (contents are replaced)."
    "$PY" -m venv --clear venv || { echo "ERROR: could not create venv"; finish 1; }
fi

# ---- 3. Install the libraries with THIS environment's pip ------------
echo "[3/5] Installing requirements (1-3 minutes) ..."
"$VPY" -m pip install --upgrade pip --quiet || { echo "ERROR: pip upgrade failed"; finish 1; }
"$VPY" -m pip install -r requirements.txt || { echo "ERROR: installation failed"; finish 1; }

# ---- 4. Register the Jupyter kernel for VS Code -----------------------
echo "[4/5] Registering kernel 'Python (Manchester venv)' ..."
"$VPY" -m ipykernel install --user --name manchester-venv \
    --display-name "Python (Manchester venv)" \
    || { echo "ERROR: kernel registration failed"; finish 1; }

# ---- 5. Prove it works: unit tests + full pipeline --------------------
echo "[5/5] Running unit tests and the analysis pipeline ..."
"$VPY" -m pytest -q || { echo "ERROR: tests failed"; finish 1; }
"$VPY" -m src.pipeline.run_pipeline || { echo "ERROR: pipeline failed"; finish 1; }

echo ""
echo "SETUP COMPLETE."
echo "Terminal:  source venv/bin/activate"
echo "VS Code :  Select Kernel > Jupyter Kernel... > Python (Manchester venv)"
finish 0
