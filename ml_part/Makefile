VENV     := .venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
OUT_DIR  := out

.PHONY: all venv install train clean fclean re

all: train

$(VENV)/bin/activate:
	python3.11 -m venv $(VENV)

venv: $(VENV)/bin/activate

install: venv
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q

$(OUT_DIR):
	mkdir -p $(OUT_DIR)/models

train: install $(OUT_DIR)
	$(PYTHON) src/model.py

clean:
	rm -rf $(OUT_DIR)

fclean: clean
	rm -rf $(VENV)

re: fclean all
