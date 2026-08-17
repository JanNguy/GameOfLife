PYTHON_VERSION := 3.11
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
STAMP := $(VENV)/.installed

.PHONY: all setup venv install data ml game serveur client client-setup dev clean fclean re

# Full pipeline: data → ml → agents
all: data ml game

setup: $(STAMP)

install: setup

venv: $(STAMP)

$(STAMP): requirements.txt
	@if [ ! -x "$(PYTHON)" ] || ! grep -q "^version = $(PYTHON_VERSION)" "$(VENV)/pyvenv.cfg"; then \
		rm -rf "$(VENV)"; \
		python$(PYTHON_VERSION) -m venv "$(VENV)"; \
	fi
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@touch "$(STAMP)"

# Process UCI dataset → data_part/out/out_profiles.csv
data: setup
	$(MAKE) -C data_part all

# Train decision model → ml_part/out/models/
ml: setup
	$(MAKE) -C ml_part all

# Sample agents from profiles → game/agents.json
game: setup
	$(MAKE) -C game run

# Start FastAPI backend (requires data pipeline to have run)
serveur: setup
	$(MAKE) -C serveur run

# Start Vite dev server
client:
	cd Client && pnpm dev

client-setup:
	cd Client && pnpm install

# Start the API and Vite together so the client's /exec proxy always has a backend.
dev: setup client-setup
	@$(MAKE) -C serveur run & server_pid=$$!; \
	trap 'kill $$server_pid 2>/dev/null' INT TERM EXIT; \
	cd Client && pnpm dev

clean:
	$(MAKE) -C data_part clean
	$(MAKE) -C ml_part clean
	$(MAKE) -C game clean
	$(MAKE) -C serveur clean

fclean: clean
	$(MAKE) -C data_part fclean
	$(MAKE) -C ml_part fclean
	$(MAKE) -C game fclean
	$(MAKE) -C serveur fclean
	rm -f game/agents.json out_profiles.json
	rm -rf Client/node_modules Client/dist
	rm -rf $(VENV)

re: fclean all
