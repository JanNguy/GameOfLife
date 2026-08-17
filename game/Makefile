ROOT_DIR := ..
VENV := $(ROOT_DIR)/.venv
PYTHON := $(VENV)/bin/python

.PHONY: all setup install run clean fclean re

all: run

setup:
	$(MAKE) -C $(ROOT_DIR) setup

install: setup

run: setup
	$(PYTHON) game.py

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +

fclean: clean
	true

re: fclean all
