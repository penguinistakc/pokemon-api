# PYT200-064 Class Demos

## Pokemon API (`main.py`)

A simple script that fetches data from the PokeAPI at https://pokeapi.co/api/v2/pokemon/{pokemon_name}. Demonstrates basic use of the `requests` library: making GET requests, checking status codes, and parsing JSON responses.

```bash
uv run python main.py
```

## Senator Web Scraper (`scrape_senators.py`)

Scrapes the list of current U.S. senators from Wikipedia, including their state, party affiliation, footnotes, and official Senate website URLs. Demonstrates `requests`, `beautifulsoup4`, `re`, and `concurrent.futures`.

```bash
uv run python scrape_senators.py
```

---

# Code Walkthrough: `scrape_senators.py`

## Step 1: Setting Up the Request

```python
HEADERS = {"User-Agent": "PYT200-064 Class Demo (educational project)"}
response = requests.get(url, headers=HEADERS)
```

Wikipedia returns a **403 Forbidden** error if you don't include a `User-Agent` header. Many websites enforce this — it's one of the first real-world obstacles you'll encounter when scraping. The `requests` library makes it easy to pass custom headers as a dictionary. The `User-Agent` string can be anything descriptive; we identify ourselves as an educational project.

## Step 2: Parsing HTML with BeautifulSoup

```python
soup = BeautifulSoup(response.text, "html.parser")
```

This creates a parsed tree of the entire HTML document. From here, we can search for elements by tag name, CSS class, attributes, and more — rather than trying to parse raw HTML strings ourselves.

## Step 3: Finding the Right Table

The Wikipedia page has **four** sortable tables, not one. The first three are leadership summaries. The senators table is the fourth:

```python
tables = soup.find_all("table", class_="sortable")
table = tables[3]
```

This is a common scraping pitfall: assuming there's only one element matching your criteria. Always inspect the page to see what `find_all` actually returns.

## Step 4: Navigating the Row Structure

This is the core scraping challenge. The HTML table uses a `rowspan` attribute to merge cells:

```html
<tr>
  <td rowspan="2">Alabama</td>     <!-- spans BOTH senator rows -->
  <td>...</td>                      <!-- portrait image -->
  <th>Tommy Tuberville</th>         <!-- senator name -->
  <td></td>                         <!-- party color (empty cell with background color) -->
  <td>Republican</td>               <!-- party name -->
  ...
</tr>
<tr>
  <!-- NO state cell here — it's covered by the rowspan above -->
  <td>...</td>                      <!-- portrait -->
  <th>Katie Britt</th>              <!-- senator name -->
  <td></td>                         <!-- party color -->
  <td>Republican</td>               <!-- party name -->
  ...
</tr>
```

Our parsing loop tracks the "current state" and updates it only when a new state cell appears:

```python
current_state = None

for row in rows:
    state_cell = row.find("td", rowspan="2")
    if state_cell:
        current_state = state_cell.get_text(strip=True)

    name_cell = row.find("th")
    if name_cell and current_state:
        name = name_cell.get_text(strip=True)
```

### HTML tags we search for and why

| Tag / Selector | What it finds | Why it matters |
|---|---|---|
| `<table class="sortable">` | All sortable wikitables on the page | Locates the senators table (the 4th one) |
| `<tbody>` | The table body | Separates data rows from the header row |
| `<tr>` | Table rows | Each row is one senator |
| `<td rowspan="2">` | State name cells | These span two rows (one per senator pair). The `rowspan` attribute is the key to knowing when a new state begins |
| `<th>` | Senator names (row headers) | Wikipedia uses `<th>` (header cells), not `<td>`, for senator names. This is semantically correct HTML — the senator name identifies the row — but it surprises students who expect all data in `<td>` elements |
| `<td>` siblings after `<th>` | Party color cell + party name | We use `find_next_sibling("td")` twice to skip the empty color cell and reach the party text |
| `<sup>` | Superscript footnote markers like `[o]` | These appear inline in the party cell and need to be extracted before reading the clean party text |
| `<a href="#cite_note-...">` | Links inside footnote markers | Points to the footnote's `id` in the references section at the bottom of the page |
| `<li id="cite_note-...">` | Footnote list items | Contains the actual footnote text we want |
| `<span class="mw-cite-backlink">` | The `^ a b` back-reference prefix in footnotes | We skip this span and instead target `reference-text` to get clean footnote content |
| `<span class="reference-text">` | The actual footnote content | Cleaner than extracting all text from the `<li>` and trying to strip artifacts |
| `<table class="infobox">` | The infobox sidebar on individual senator pages | Contains the "Website" row with the Senate URL |

## Step 5: Cleaning Up Footnotes with `re`

Some party cells contain Wikipedia footnote markers like `[o]` or `[q]`. We extract the actual footnote text from the references section at the bottom of the page. However, that text still contains inline citation numbers like `[15]`, `[4]`, `[5]` that we need to strip:

```python
notes = re.sub(r"\s*\[\s*\d+\s*\]", "", notes).strip()
```

### Breaking down the regex

The `re.sub(pattern, replacement, string)` function finds all matches of `pattern` in `string` and replaces them with `replacement` (here, an empty string — effectively deleting them).

The pattern `\s*\[\s*\d+\s*\]` matches bracketed numbers with optional surrounding whitespace:

| Component | Matches | Example |
|---|---|---|
| `\s*` | Zero or more whitespace characters before the bracket | the space before ` [15]` |
| `\[` | A literal opening bracket | `[` (escaped because `[` is special in regex) |
| `\s*` | Optional whitespace inside the bracket | handles `[ 15]` or `[15 ]` |
| `\d+` | One or more digits | `15`, `4`, `5` |
| `\s*` | Optional whitespace before closing bracket | |
| `\]` | A literal closing bracket | `]` (also escaped) |

Without this cleanup, the note for Angus King would read:

> Angus King of Maine and Bernie Sanders of Vermont join meetings of the Senate Democratic Caucus . [15] [4] [5]

After `re.sub`, it becomes:

> Angus King of Maine and Bernie Sanders of Vermont join meetings of the Senate Democratic Caucus .

The `\s*` outside the brackets also consumes the space *before* each citation, preventing leftover gaps where the citations were removed. The final `.strip()` trims any remaining leading or trailing whitespace.

## Step 6: Fetching Senate Websites in Parallel

Each senator's name cell contains a link to their individual Wikipedia page (e.g., `/wiki/Katie_Britt`). On that page, an **infobox** sidebar contains a "Website" row with their official Senate URL.

Fetching 100 pages one at a time would be slow. Since each request is **I/O-bound** (we're waiting for Wikipedia to respond, not doing heavy computation), we use threads:

```python
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_index = {
        executor.submit(get_senate_website, senator[3]): i
        for i, senator in enumerate(senators)
        if senator[3]
    }
    for future in as_completed(future_to_index):
        idx = future_to_index[future]
        try:
            websites[idx] = future.result()
        except Exception as e:
            print(f"  Warning: could not fetch website for {senators[idx][0]}: {e}")
```

`max_workers=10` keeps 10 requests in flight at once — roughly 10x faster than serial, while being respectful to Wikipedia's servers. `as_completed` lets us process results as they arrive rather than waiting in order, and the `try/except` ensures one failed request doesn't crash the whole batch.

This is a great teaching contrast: **threads** work well for I/O-bound work like HTTP requests, while `ProcessPoolExecutor` would be the choice for CPU-bound work like heavy computation.

---

## Development Insights

These observations came up during the iterative development of the script:

1. **Wikipedia blocks bare requests.** The very first run failed with a 403. Many websites require a `User-Agent` header — a good early lesson in reading HTTP responses and adapting your request parameters.

2. **HTML tables rarely map cleanly to flat data.** The `rowspan="2"` on state cells means you can't just read every cell from every row. You need to track state across rows. This kind of structural complexity is the norm, not the exception, when scraping real websites.

3. **`<th>` vs `<td>` matters.** Senator names are in `<th>` elements (row headers), not `<td>`. This is semantically correct HTML — the name *identifies* the row — but trips up code that only searches for `<td>`.

4. **Navigate relative to landmarks, not by position.** Rather than counting column indices (which shift depending on whether the `rowspan` state cell is present), the script navigates relative to the `<th>` name cell using `find_next_sibling`. This is more robust when rows have inconsistent column counts.

5. **Use HTML structure over string manipulation.** Wikipedia footnote `<li>` elements contain two `<span>` children: `mw-cite-backlink` (the `^ a b` navigation) and `reference-text` (the actual content). Targeting `reference-text` directly is far cleaner than extracting all text and trying to regex away the navigation artifacts.

6. **Threads for I/O, processes for CPU.** Fetching 100 pages serially would take minutes. `ThreadPoolExecutor` with 10 workers keeps multiple requests in flight without the complexity of async code, making it an accessible introduction to concurrency.
