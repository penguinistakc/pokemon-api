import requests
from unittest.mock import Mock
from main import get_pokemon_data


class TestGetPokemonData:
    """Test suite for the get_pokemon_data function"""

    def test_successful_pokemon_fetch(self, mocker):
        """Test successful API call returns Pokemon data as dictionary"""
        # Mock response data
        mock_data = {
            "name": "pikachu",
            "height": 4,
            "weight": 60,
            "types": [
                {"type": {"name": "electric"}}
            ]
        }

        # Mock the requests.get call
        mock_response = Mock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        mocker.patch('requests.get', return_value=mock_response)

        # Call the function
        result = get_pokemon_data("pikachu")

        # Assertions
        assert result is not None
        assert result["name"] == "pikachu"
        assert result["height"] == 4
        assert result["weight"] == 60
        assert len(result["types"]) == 1
        assert result["types"][0]["type"]["name"] == "electric"

        # Verify the API was called with correct URL
        requests.get.assert_called_once_with("https://pokeapi.co/api/v2/pokemon/pikachu")

    def test_pokemon_name_case_insensitive(self, mocker):
        """Test that Pokemon names are converted to lowercase"""
        mock_response = Mock()
        mock_response.json.return_value = {"name": "charizard"}
        mock_response.raise_for_status.return_value = None
        mocker.patch('requests.get', return_value=mock_response)

        # Test with uppercase name
        get_pokemon_data("CHARIZARD")

        # Verify lowercase conversion
        requests.get.assert_called_once_with("https://pokeapi.co/api/v2/pokemon/charizard")

    def test_pokemon_name_mixed_case(self, mocker):
        """Test that mixed case Pokemon names are handled correctly"""
        mock_response = Mock()
        mock_response.json.return_value = {"name": "bulbasaur"}
        mock_response.raise_for_status.return_value = None
        mocker.patch('requests.get', return_value=mock_response)

        # Test with mixed case
        get_pokemon_data("BuLbAsAuR")

        # Verify lowercase conversion
        requests.get.assert_called_once_with("https://pokeapi.co/api/v2/pokemon/bulbasaur")

    def test_http_error_404(self, mocker, capsys):
        """Test handling of 404 error (Pokemon not found)"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mocker.patch('requests.get', return_value=mock_response)

        result = get_pokemon_data("notapokemon")

        assert result is None
        captured = capsys.readouterr()
        assert "Error fetching Pokemon data" in captured.out

    def test_connection_error(self, mocker, capsys):
        """Test handling of connection errors"""
        mocker.patch('requests.get', side_effect=requests.exceptions.ConnectionError("Connection failed"))

        result = get_pokemon_data("pikachu")

        assert result is None
        captured = capsys.readouterr()
        assert "Error fetching Pokemon data" in captured.out

    def test_timeout_error(self, mocker, capsys):
        """Test handling of timeout errors"""
        mocker.patch('requests.get', side_effect=requests.exceptions.Timeout("Request timeout"))

        result = get_pokemon_data("pikachu")

        assert result is None
        captured = capsys.readouterr()
        assert "Error fetching Pokemon data" in captured.out

    def test_generic_request_exception(self, mocker, capsys):
        """Test handling of generic request exceptions"""
        mocker.patch('requests.get', side_effect=requests.exceptions.RequestException("Generic error"))

        result = get_pokemon_data("pikachu")

        assert result is None
        captured = capsys.readouterr()
        assert "Error fetching Pokemon data" in captured.out

    def test_returns_dictionary_type(self, mocker):
        """Test that the function returns a dictionary when successful"""
        mock_data = {"name": "mewtwo", "height": 20, "weight": 1220}
        mock_response = Mock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        mocker.patch('requests.get', return_value=mock_response)

        result = get_pokemon_data("mewtwo")

        assert isinstance(result, dict)

    def test_complex_pokemon_data(self, mocker):
        """Test with complex Pokemon data including multiple types"""
        mock_data = {
            "name": "charizard",
            "height": 17,
            "weight": 905,
            "types": [
                {"slot": 1, "type": {"name": "fire", "url": "https://pokeapi.co/api/v2/type/10/"}},
                {"slot": 2, "type": {"name": "flying", "url": "https://pokeapi.co/api/v2/type/3/"}}
            ],
            "abilities": [
                {"ability": {"name": "blaze"}}
            ],
            "stats": [
                {"base_stat": 78, "stat": {"name": "hp"}}
            ]
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        mocker.patch('requests.get', return_value=mock_response)

        result = get_pokemon_data("charizard")

        assert result is not None
        assert result["name"] == "charizard"
        assert len(result["types"]) == 2
        assert result["types"][0]["type"]["name"] == "fire"
        assert result["types"][1]["type"]["name"] == "flying"
        assert "abilities" in result
        assert "stats" in result

