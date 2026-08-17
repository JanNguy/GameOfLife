ROOT_DIR := ..
VENV := $(ROOT_DIR)/.venv
PYTHON := $(VENV)/bin/python
OUT_DIR := out

.PHONY: all setup install train clean fclean re

all: train

setup:
	$(MAKE) -C $(ROOT_DIR) setup

install: setup

$(OUT_DIR):
	mkdir -p $(OUT_DIR)/models

train: setup $(OUT_DIR)
	$(PYTHON) src/model.py

clean:
	rm -rf $(OUT_DIR)

fclean: clean
	true

re: fclean all
