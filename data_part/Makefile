ROOT_DIR := ..
VENV := $(ROOT_DIR)/.venv
PYTHON := $(VENV)/bin/python
OUT_DIR := out

.PHONY: all setup install run data synthesis clean fclean re

all: data synthesis

setup:
	$(MAKE) -C $(ROOT_DIR) setup

install: setup

$(OUT_DIR):
	mkdir -p $(OUT_DIR)

data: setup $(OUT_DIR)
	$(PYTHON) src/data_read.py

synthesis: setup
	$(PYTHON) src/out_synthesis.py

run: all

clean:
	rm -rf $(OUT_DIR)

fclean: clean
	true

re: fclean all
