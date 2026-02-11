import requests

def get_pokemon_data(pokemon_name):
    """
    Fetch Pokemon data from the PokeAPI.

    Args:
        pokemon_name: Name of the Pokemon to fetch

    Returns:
        Dictionary containing Pokemon data, or None if request fails
    """
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Pokemon data: {e}")
        return None

if __name__ == "__main__":
    pokemon_name = input("Enter a Pokemon name: ")
    show_raw = input("Show complete raw JSON? (y/n): ").lower().strip() == 'y'

    data = get_pokemon_data(pokemon_name)

    if data:
        if show_raw:
            import json
            print("\n" + "="*50)
            print("COMPLETE RAW JSON DATA")
            print("="*50)
            print(json.dumps(data, indent=2))
        else:
            print(f"\nPokemon: {data['name'].capitalize()}")
            print(f"Height: {data['height']}")
            print(f"Weight: {data['weight']}")
            print(f"Types: {', '.join([t['type']['name'] for t in data['types']])}")
    else:
        print("Failed to retrieve Pokemon data.")
