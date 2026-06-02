VENV     := .venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
OUT_DIR  := out

.PHONY: all venv install run data synthesis clean fclean re

all: data synthesis

run: data synthesis

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

venv: $(VENV)/bin/activate

install: venv
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt

$(OUT_DIR):
	mkdir -p $(OUT_DIR)

data: install $(OUT_DIR)
	$(PYTHON) src/data_read.py

synthesis: install
	$(PYTHON) src/out_synthesis.py

clean:
	rm -rf $(OUT_DIR)

fclean: clean
	rm -rf $(VENV)

re: fclean all
