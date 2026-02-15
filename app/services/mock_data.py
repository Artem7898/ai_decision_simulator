async def get_mock_cost_of_living(city: str, country: str):
    """Возвращает mock-данные о стоимости жизни"""
    mock_data = {
        "berlin": {
            "cost_of_living_index": 65.5,
            "rent_index": 42.1,
            "groceries_index": 58.3,
            "restaurant_price_index": 70.2
        },
        "amsterdam": {
            "cost_of_living_index": 78.2,
            "rent_index": 68.9,
            "groceries_index": 62.4,
            "restaurant_price_index": 75.1
        }
    }
    key = city.lower()
    return mock_data.get(key, {
        "cost_of_living_index": 65.0,
        "rent_index": 50.0,
        "groceries_index": 60.0,
        "restaurant_price_index": 65.0
    })