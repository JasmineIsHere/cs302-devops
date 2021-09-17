import json
import pytest


def call(client, path, method='GET', body=None):
    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }

    if method == 'POST':
        response = client.post(path, data=json.dumps(body), headers=headers)
    elif method == 'PUT':
        response = client.put(path, data=json.dumps(body), headers=headers)
    elif method == 'PATCH':
        response = client.patch(path, data=json.dumps(body), headers=headers)
    elif method == 'DELETE':
        response = client.delete(path)
    else:
        response = client.get(path)

    return {
        "json": json.loads(response.data.decode('utf-8')),
        "code": response.status_code
    }


@pytest.mark.dependency()
def test_health(client):
    result = call(client, 'health')
    assert result['code'] == 200


@pytest.mark.dependency()
def test_get_all(client):
    result = call(client, 'games')
    assert result['code'] == 200
    assert result['json']['data']['games'] == [
      {
        "game_id": 1,
        "platform": "SNES",
        "price": 40.0,
        "stock": 15,
        "title": "Final Fantasy VI"
      },
      {
        "game_id": 2,
        "platform": "Switch",
        "price": 60.5,
        "stock": 200,
        "title": "Legend of Zelda Skyward Sword"
      },
      {
        "game_id": 3,
        "platform": "GameCube",
        "price": 18.7,
        "stock": 1,
        "title": "Skies of Arcadia"
      },
      {
        "game_id": 7,
        "platform": "Mega Drive",
        "price": 25.55,
        "stock": 5,
        "title": "Phantasy Star IV"
      },
      {
        "game_id": 9,
        "platform": "MS-DOS",
        "price": 100.0,
        "stock": 1,
        "title": "Mario is Missing"
      }
    ]


# This is not a dependency per se (the tests can be
# executed in any order). But if 'test_get_all' does
# not pass, there's no point in running any other
# test, so may as well skip them.

@pytest.mark.dependency(depends=['test_get_all'])
def test_one_valid(client):
    result = call(client, 'games/2')
    assert result['code'] == 200
    assert result['json']['data'] == {
        "game_id": 2,
        "platform": "Switch",
        "price": 60.5,
        "stock": 200,
        "title": "Legend of Zelda Skyward Sword"
    }


@pytest.mark.dependency(depends=['test_get_all'])
def test_one_invalid(client):
    result = call(client, 'games/55')
    assert result['code'] == 404
    assert result['json'] == {
        "message": "Game not found."
    }


@pytest.mark.dependency(depends=['test_get_all'])
def test_replace_existing_game(client):
    result = call(client, 'games/1', 'PUT', {
        "platform": "SNES",
        "price": 88,
        "stock": 8,
        "title": "Final Fantasy VI"
    })
    assert result['code'] == 200
    assert result['json']['data'] == {
        "game_id": 1,
        "platform": "SNES",
        "price": 88,
        "stock": 8,
        "title": "Final Fantasy VI"
    }


@pytest.mark.dependency(depends=['test_get_all'])
def test_update_existing_game(client):
    result = call(client, 'games/1', 'PATCH', {
        "price": 88,
        "stock": 8
    })
    assert result['code'] == 200
    assert result['json']['data'] == {
        "game_id": 1,
        "platform": "SNES",
        "price": 88,
        "stock": 8,
        "title": "Final Fantasy VI"
    }


@pytest.mark.dependency(depends=['test_get_all'])
def test_reserve_existing_game(client):
    result = call(client, 'games/1', 'PATCH', {
        "reserve": 5
    })
    assert result['code'] == 200
    assert result['json']['data'] == {
        "game_id": 1,
        "platform": "SNES",
        "price": 40,
        "stock": 10,
        "title": "Final Fantasy VI"
    }


@pytest.mark.dependency(depends=['test_get_all'])
def test_reserve_existing_game_all(client):
    result = call(client, 'games/1', 'PATCH', {
        "reserve": 15
    })
    assert result['code'] == 200
    assert result['json']['data'] == {
        "game_id": 1,
        "platform": "SNES",
        "price": 40,
        "stock": 0,
        "title": "Final Fantasy VI"
    }


@pytest.mark.dependency(depends=['test_get_all'])
def test_unreserve_existing_game(client):
    result = call(client, 'games/1', 'PATCH', {
        "reserve": -5
    })
    assert result['code'] == 200
    assert result['json']['data'] == {
        "game_id": 1,
        "platform": "SNES",
        "price": 40,
        "stock": 20,
        "title": "Final Fantasy VI"
    }


@pytest.mark.dependency(depends=['test_get_all'])
def test_reserve_existing_game_fail(client):
    result = call(client, 'games/1', 'PATCH', {
        "reserve": 16
    })
    assert result['code'] == 500


@pytest.mark.dependency(depends=['test_get_all'])
def test_reserve_nonexisting_game(client):
    result = call(client, 'games/555', 'PATCH', {
        "reserve": 16
    })
    assert result['code'] == 404


@pytest.mark.dependency(depends=['test_get_all'])
def test_create_no_body(client):
    result = call(client, 'games', 'POST', {})
    assert result['code'] == 500


@pytest.mark.dependency(depends=['test_get_all', 'test_create_no_body'])
def test_create_one_game(client):
    result = call(client, 'games', 'POST', {
        "platform": "SNES",
        "price": 45.0,
        "stock": 5,
        "title": "Final Fantasy V"
    })
    assert result['code'] == 201
    assert result['json']['data'] == {
        "game_id": 10,
        "platform": "SNES",
        "price": 45.0,
        "stock": 5,
        "title": "Final Fantasy V"
    }


@pytest.mark.dependency(depends=['test_create_one_game'])
def test_replace_new_game(client):
    call(client, 'games', 'POST', {
        "platform": "SNES",
        "price": 45.0,
        "stock": 5,
        "title": "Final Fantasy V"
    })
    result = call(client, 'games/10', 'PUT', {
        "platform": "PS1",
        "price": 45.0,
        "stock": 5,
        "title": "Final Fantasy VII"
    })
    assert result['code'] == 200
    assert result['json']['data'] == {
        "game_id": 10,
        "platform": "PS1",
        "price": 45.0,
        "stock": 5,
        "title": "Final Fantasy VII"
    }


@pytest.mark.dependency(depends=['test_create_one_game'])
def test_update_new_game(client):
    call(client, 'games', 'POST', {
        "platform": "SNES",
        "price": 45.0,
        "stock": 5,
        "title": "Final Fantasy V"
    })
    result = call(client, 'games/10', 'PATCH', {
        "platform": "PS1",
        "title": "Final Fantasy VII"
    })
    assert result['code'] == 200
    assert result['json']['data'] == {
        "game_id": 10,
        "platform": "PS1",
        "price": 45.0,
        "stock": 5,
        "title": "Final Fantasy VII"
    }


@pytest.mark.dependency(depends=['test_get_all'])
def test_delete_game(client):
    result = call(client, 'games/2', 'DELETE')
    assert result['code'] == 200
    assert result['json']['data'] == {
        "game_id": 2
    }


@pytest.mark.dependency(depends=['test_delete_game'])
def test_deleted_game(client):
    call(client, 'games/2', 'DELETE')
    result = call(client, 'games/2', 'GET')
    assert result['code'] == 404
    assert result['json'] == {
        "message": "Game not found."
    }
