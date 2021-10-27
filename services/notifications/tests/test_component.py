import json
import mysql.connector
import pika
import pytest
import time
from os import environ
from urllib.parse import urlparse


db_url = urlparse(environ.get('db_conn'))


def get_database_connection():
    cnx = mysql.connector.connect(
            user=db_url.username,
            password=db_url.password,
            host=db_url.hostname,
            port=db_url.port,
            database='notification'
            )

    return cnx


@pytest.fixture
def refresh_database():
    cnx = get_database_connection()

    cursor = cnx.cursor()

    cursor.execute('''DROP TABLE IF EXISTS `notification`;''')
    cursor.execute('''CREATE TABLE `notification` (
                      `notification_id` int NOT NULL AUTO_INCREMENT,
                      `email` varchar(64) NOT NULL,
                      `data` mediumtext NOT NULL,
                      PRIMARY KEY (`notification_id`)
                      ) ENGINE=InnoDB AUTO_INCREMENT=1
                      DEFAULT CHARSET=utf8;''')

    cnx.commit()
    cnx.close()


def send_message(exchange_name, key, body_dict):
    hostname = environ.get('rabbitmq_host')
    port = environ.get('rabbitmq_port')

    parameters = pika.ConnectionParameters(host=hostname,
                                           port=port
                                           )

    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()

    channel.basic_publish(
        exchange=exchange_name, routing_key=key,
        body=json.dumps(body_dict),
        properties=pika.BasicProperties(delivery_mode=2))

    connection.close()


@pytest.mark.dependency()
def test_new_order(refresh_database):
    send_message("notifications.topic", "order.new", {
        "email": "phris@coskitt.com",
        "data": {
            "someThing": "someMessage"
        }
    })

    # wait for the message to be processed
    time.sleep(1)

    cnx = get_database_connection()

    cursor = cnx.cursor()

    cursor.execute("SELECT * FROM `notification`;")

    row = cursor.fetchone()

    email = row[1]
    data = row[2]

    cnx.close()

    assert email == "phris@coskitt.com"
    assert data == json.dumps({
            "someThing": "someMessage"
        })


@pytest.mark.dependency()
def test_cancel_order(refresh_database):
    send_message("notifications.topic", "order.cancel", {
        "email": "haniel@danley.smu.edu.sg",
        "data": {
            "someThing": "your order got cancelled ah!"
        }
    })

    # wait for the message to be processed
    time.sleep(1)

    cnx = get_database_connection()

    cursor = cnx.cursor()

    cursor.execute("SELECT * FROM `notification`;")

    row = cursor.fetchone()

    email = row[1]
    data = row[2]

    cnx.close()

    assert email == "haniel@danley.smu.edu.sg"
    assert data == json.dumps({
            "someThing": "your order got cancelled ah!"
        })


@pytest.mark.dependency()
def test_illegal_routing_key(refresh_database):
    send_message("notifications.topic", "phris.coskitt", {
        "email": "yorkshire@is.great.uk",
        "data": "This message should not reach the queue!"
    })

    # wait for the message to be processed
    time.sleep(1)

    cnx = get_database_connection()

    cursor = cnx.cursor()

    cursor.execute("SELECT * FROM `notification`;")

    row = cursor.fetchone()

    cnx.close()

    assert row is None
