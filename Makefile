# Short commands for the PyChrono simulation. Requires conda (macOS/Linux).
# Without make: run the raw commands listed in AGENTS.md.

ENV ?= chrono
SIM := 03_Simulation_PyChrono
ifndef PY
PY := $(shell conda run -n $(ENV) python -c "import sys; print(sys.executable)" 2>/dev/null)
endif

.DEFAULT_GOAL := help
.PHONY: help setup check-env test validate sim diag replay hooks clean

help:  ## List the available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

setup:  ## Create the conda env and install the git hooks
	conda create -y -n $(ENV) -c projectchrono -c conda-forge python=3.11 pychrono matplotlib pillow
	$(MAKE) hooks

check-env:  ## Check that PyChrono imports without the graphics extensions
	@test -n "$(PY)" || { echo "conda env '$(ENV)' not found: run make setup"; exit 1; }
	$(PY) $(SIM)/chrono_headless.py

test:  ## Fast unit tests of the physics laws (no PyChrono dynamics, <1 s)
	@test -n "$(PY)" || { echo "conda env '$(ENV)' not found: run make setup"; exit 1; }
	$(PY) -m unittest discover -s $(SIM) -p test_granulobot_physics.py

validate:  ## PyChrono dynamics checks (~15 s)
	$(PY) $(SIM)/validation_modele.py

sim:  ## Run the simulator: make sim NAME=run_name ARGS="--duree 0.2 --sans-gif"
	$(PY) $(SIM)/test_3_granulobots.py --sortie runs/$(or $(NAME),sim) $(ARGS)

diag:  ## Analyse a run: make diag CSV=runs/sim.csv
	$(PY) $(SIM)/diagnostic_accrochage.py $(CSV)

replay:  ## Rebuild a GIF from a CSV without rerunning: make replay CSV=runs/sim.csv
	$(PY) $(SIM)/test_3_granulobots.py --rejouer $(CSV)

hooks:  ## Install the git hooks from tools/git-hooks (redo after every fresh clone)
	cp tools/git-hooks/commit-msg tools/git-hooks/pre-commit .git/hooks/
	chmod +x .git/hooks/commit-msg .git/hooks/pre-commit
	@echo "git hooks installed"

clean:  ## Remove Python caches (never touches runs/ or results/)
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
