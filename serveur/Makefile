VENV   := .venv
PIP    := $(VENV)/bin/pip

.PHONY: all venv install run clean fclean re

all: run

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

venv: $(VENV)/bin/activate

install: venv
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt

run: install
	$(VENV)/bin/uvicorn main:app --reload

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +

fclean: clean
	rm -rf $(VENV)

re: fclean all
