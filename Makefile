.PHONY: all data ml game serveur client clean fclean

# Full pipeline: data → ml → agents
all: data ml game

# Process UCI dataset → data_part/out/out_profiles.csv
data:
	$(MAKE) -C data_part all

# Train decision model → ml_part/out/models/
ml:
	$(MAKE) -C ml_part all

# Sample agents from profiles → game/agents.json
game:
	$(MAKE) -C game run

# Start FastAPI backend (requires data pipeline to have run)
serveur:
	$(MAKE) -C serveur run

# Start Vite dev server
client:
	cd Client && pnpm install && pnpm dev

clean:
	$(MAKE) -C data_part clean
	$(MAKE) -C ml_part clean
	$(MAKE) -C game clean
	$(MAKE) -C serveur clean

fclean:
	$(MAKE) -C data_part fclean
	$(MAKE) -C ml_part fclean
	$(MAKE) -C game fclean
	$(MAKE) -C serveur fclean
	rm -f game/agents.json out_profiles.json
	rm -rf Client/node_modules Client/dist
