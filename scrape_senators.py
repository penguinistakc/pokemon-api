import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

WIKI_BASE = "https://en.wikipedia.org"
HEADERS = {"User-Agent": "PYT200-064 Class Demo (educational project)"}


def get_senate_website(wiki_path):
    """
    Given a senator's Wikipedia path (e.g. /wiki/Katie_Britt),
    fetch their page and extract the Senate website URL from the infobox.
    """
    url = f"{WIKI_BASE}{wiki_path}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    infobox = soup.find("table", class_="infobox")
    if infobox:
        for th in infobox.find_all("th"):
            if "Website" in th.get_text():
                td = th.find_next_sibling("td")
                if td:
                    link = td.find("a")
                    if link:
                        return link.get("href", "")
    return ""


def get_senators():
    """
    Scrape the list of current U.S. senators and their states
    from Wikipedia, then fetch each senator's website in parallel.

    Returns:
        List of tuples: (senator_name, state, party, website, notes)
    """
    url = f"{WIKI_BASE}/wiki/List_of_current_United_States_senators"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # The page has several sortable tables; the senators table is the
    # largest one, with "State" and "Senator" in its header row.
    tables = soup.find_all("table", class_="sortable")
    table = tables[3]
    tbody = table.find("tbody")
    rows = tbody.find_all("tr")

    senators = []
    current_state = None

    for row in rows:
        # State cells have rowspan="2", spanning both senator rows
        state_cell = row.find("td", rowspan="2")
        if state_cell:
            current_state = state_cell.get_text(strip=True)

        # Senator names are in <th> row header elements
        name_cell = row.find("th")
        if name_cell and current_state:
            name = name_cell.get_text(strip=True)
            wiki_link = name_cell.find("a")
            wiki_path = wiki_link["href"] if wiki_link else ""

            # Party is two <td> siblings after the <th>: an empty color cell, then the party name
            party_cell = name_cell.find_next_sibling("td").find_next_sibling("td")

            # Extract footnote references before getting the clean party text
            notes = ""
            footnotes = party_cell.find_all("sup")
            if footnotes:
                for sup in footnotes:
                    link = sup.find("a")
                    if link and link.get("href", "").startswith("#cite_note"):
                        ref_id = link["href"].lstrip("#")
                        ref_li = soup.find("li", id=ref_id)
                        if ref_li:
                            # The footnote contains a backlink span ("^ a b")
                            # and a reference-text span with the actual note
                            ref_text = ref_li.find("span", class_="reference-text")
                            if ref_text:
                                notes = ref_text.get_text(" ", strip=True)
                                # Remove bracketed citation numbers like [15]
                                notes = re.sub(r"\s*\[\s*\d+\s*\]", "", notes).strip()
                    sup.decompose()  # Remove <sup> so it doesn't appear in party text

            party = party_cell.get_text(strip=True)
            senators.append((name, current_state, party, wiki_path, notes))

    # Fetch all Senate website URLs in parallel using a thread pool
    print(f"Fetching website URLs for {len(senators)} senators...")
    websites = [""] * len(senators)

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_index = {
            executor.submit(get_senate_website, senator[3]): i
            for i, senator in enumerate(senators)
            if senator[3]  # only if we have a wiki path
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                websites[idx] = future.result()
            except Exception as e:
                print(f"  Warning: could not fetch website for {senators[idx][0]}: {e}")

    # Replace wiki_path with the actual website URL
    senators = [
        (name, state, party, websites[i], notes)
        for i, (name, state, party, _, notes) in enumerate(senators)
    ]

    return senators


if __name__ == "__main__":
    senators = get_senators()
    print(f"\n{'Senator':<30} {'State':<20} {'Party':<15} {'Website'}")
    print("-" * 110)
    for name, state, party, website, notes in senators:
        print(f"{name:<30} {state:<20} {party:<15} {website}")
    print(f"\nTotal: {len(senators)} senators")
