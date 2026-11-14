PYTHON ?= normExpEnv/bin/python
export PYTHONPATH := $(CURDIR)/open_asr_leaderboard

.PHONY: test inspect restore replay-plan replay inference-plan

test:
	$(PYTHON) -m unittest discover -s tests -v

inspect:
	$(PYTHON) scripts/project.py inspect

restore:
	$(PYTHON) scripts/project.py restore

replay-plan:
	$(PYTHON) scripts/project.py replay --dry-run

replay:
	$(PYTHON) scripts/project.py replay

inference-plan:
	$(PYTHON) scripts/run_smoke.py --stage pilot --warmup-steps 5 --dry-run
