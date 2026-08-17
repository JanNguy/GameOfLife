ROOT_DIR := ..
VENV := $(ROOT_DIR)/.venv

.PHONY: all setup install run clean fclean re

all: run

setup:
	$(MAKE) -C $(ROOT_DIR) setup

install: setup

run: setup
	$(VENV)/bin/uvicorn main:app --host 127.0.0.1 --port 8000

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +

fclean: clean
	true

re: fclean all
