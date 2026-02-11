# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Educational project for the PYT200-064 class. Uses Python 3.14, managed with `uv`. Two demo scripts:
- `main.py` — fetches Pokemon data from the [PokeAPI](https://pokeapi.co/api/v2/pokemon/{name}) using `requests`
- `scrape_senators.py` — scrapes U.S. senator data from Wikipedia using `requests`, `beautifulsoup4`, `re`, and `concurrent.futures`

## Commands

- **Install dependencies:** `uv sync`
- **Run Pokemon demo:** `uv run python main.py`
- **Run senator scraper:** `uv run python scrape_senators.py`
- **Run all tests:** `uv run pytest`
- **Run a single test:** `uv run pytest test_main.py::TestGetPokemonData::test_name`
- **Run Jupyter notebook:** `uv run jupyter notebook`

## Architecture

- `main.py` exposes `get_pokemon_data(pokemon_name)` which returns a dict from the PokeAPI or `None` on failure. Tests in `test_main.py` mock `requests.get` using `pytest-mock`.
- `scrape_senators.py` exposes `get_senators()` (returns list of tuples) and `get_senate_website(wiki_path)`. Fetches the senator list page, then uses `ThreadPoolExecutor` to fetch 100 individual senator pages in parallel for website URLs.
