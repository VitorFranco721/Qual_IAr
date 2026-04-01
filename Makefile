.PHONY: help setup discover extract normalize validate export load all docker-build docker-run

PYTHON := python

help:
	@echo "Targets:"
	@echo "  setup        Create virtualenv and install dependencies"
	@echo "  discover     Discover and rank candidate sources"
	@echo "  extract      Download raw data (variables: from=YYYY-MM-DD to=YYYY-MM-DD)"
	@echo "  normalize    Normalize raw data into canonical schema"
	@echo "  validate     Validate normalized data"
	@echo "  export       Export normalized data to CSV/Parquet"
	@echo "  load         Load silver data into SQL (SQLite) and optional MongoDB"
	@echo "  all          Run discover, extract, normalize, validate, export and load"
	@echo "  docker-build Build the Docker image"
	@echo "  docker-run   Run the pipeline inside the Docker container"

setup:
	@if [ ! -d .venv ]; then \
		$(PYTHON) -m venv .venv; \
		. .venv/bin/activate; \
		pip install -r requirements.txt; \
	fi
	@echo "Environment setup complete"

discover:
	. .venv/bin/activate && $(PYTHON) -m br.aqi.cli discover

extract:
	. .venv/bin/activate && $(PYTHON) -m br.aqi.cli extract --since $${from:-2020-01-01} --until $${to:-today}

normalize:
	. .venv/bin/activate && $(PYTHON) -m br.aqi.cli normalize

validate:
	. .venv/bin/activate && $(PYTHON) -m br.aqi.cli validate

export:
	. .venv/bin/activate && $(PYTHON) -m br.aqi.cli export --format csv

load:
	. .venv/bin/activate && $(PYTHON) -m br.aqi.cli load

all: discover extract normalize validate export load

docker-build:
	docker build -t brasilia-aqi .

docker-run:
	docker run --rm -v $$(pwd):/app -w /app brasilia-aqi make all