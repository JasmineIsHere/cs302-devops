import json
import mysql.connector
import amqp_setup
from os import environ
from urllib.parse import urlparse


db_url = urlparse(environ.get('db_conn'))


def callback(channel, method, properties, body):
    message_body = json.loads(body)
    email = message_body['email']
    data = json.dumps(message_body['data'])
    log_data = data.replace("\n", "")

    try:
        cnx = mysql.connector.connect(
            user=db_url.username,
            password=db_url.password,
            host=db_url.hostname,
            port=db_url.port,
            database='notification'
            )

        cursor = cnx.cursor()

        cursor.execute('''
            INSERT INTO `notification` (`email`, `data`)
            VALUES (%s, %s);
            ''', (email, data))

        cnx.commit()
        cnx.close()

        print(f"SUCCESS,{email},{log_data}\n")

    except mysql.connector.Error as err:
        print(f"FAIL,{email},{log_data},{err}\n")


amqp_setup.channel.basic_consume(
    queue=amqp_setup.queue_name, on_message_callback=callback, auto_ack=True)
amqp_setup.channel.start_consuming()
