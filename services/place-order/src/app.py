import os
import json
import requests
import amqp_setup
import pika

from flask import Flask, request, jsonify
from flask_cors import CORS

if os.environ.get('stage') == 'production':
    games_service_url = os.environ.get('games_service_url')
    orders_service_url = os.environ.get('orders_service_url')
else:
    games_service_url = os.environ.get('games_service_url_internal')
    orders_service_url = os.environ.get('orders_service_url_internal')

app = Flask(__name__)

CORS(app)


@app.route("/health")
def health_check():
    return jsonify(
            {
                "message": "Service is healthy."
            }
    ), 200


@app.route("/place-order", methods=['POST'])
def place_order():
    def undo_game_reservations(cart_items):
        for (game_id, quantity) in cart_items:
            requests.patch(
                games_service_url + '/games/'
                + str(game_id),
                data=json.dumps({
                    "reserve": quantity * -1
                }),
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )

    data = request.get_json()

    # (1) Reserve the games

    game_list = []
    for order_item in data['cart_items']:
        reserve_response = requests.patch(
            games_service_url + '/games/' + str(order_item['game_id']),
            data=json.dumps({
                "reserve": order_item['quantity']
            }),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )

        if reserve_response.status_code != 200:
            undo_game_reservations(game_list)
            return jsonify(
                {
                    "message": "Unable to place order.",
                    "error": "Unable to reserve required game stock."
                }
            ), 500

        game_list.append((order_item['game_id'], order_item['quantity']))

    # (2) Create the order

    order_response = requests.post(
        orders_service_url + '/orders',
        data=json.dumps({
            "customer_email": data["customer_email"],
            "cart_items": data["cart_items"]
        }),
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    )

    if order_response.status_code != 201:
        undo_game_reservations(game_list)
        return jsonify(
            {
                "message": "Unable to place order.",
                "error": "Unable to create order record."
            }
        ), 500

    # (3) Send notification to the AMQP broker

    notification_data = {
        "email": data["customer_email"],
        "data": data["cart_items"]
    }

    connection = pika.BlockingConnection(amqp_setup.parameters)

    channel = connection.channel()

    channel.basic_publish(
        exchange=amqp_setup.exchange_name, routing_key="order.new",
        body=json.dumps(notification_data),
        properties=pika.BasicProperties(delivery_mode=2))

    connection.close()

    return jsonify(
        {
            "message": "Order placed.",
            "data": order_response.json()['data']
        }
    ), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
