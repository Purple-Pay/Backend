from confluent_kafka import Producer, Consumer, KafkaError
from confluent_kafka.cimpl import KafkaException

# Kafka broker(s) address
KAFKA_BROKER = "20.237.81.56:9092"

# SSL settings
SSL_CA_LOCATION = './purple_pay/kafka/ca.pem'
SSL_CERT_LOCATION = './purple_pay/kafka/user.pem'
SSL_KEY_LOCATION = './purple_pay/kafka/user.key'

def create_kafka_producer():
    # Producer configuration
    producer_config = {
        'bootstrap.servers': KAFKA_BROKER,
        'security.protocol': 'ssl',
        'ssl.ca.location': SSL_CA_LOCATION,
        'ssl.certificate.location': SSL_CERT_LOCATION,
        'ssl.key.location': SSL_KEY_LOCATION,
        # Add other producer settings here
    }
    return Producer(producer_config)

def create_kafka_consumer():
    # Consumer configuration
    consumer_config = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'your_consumer_group_id',
        'auto.offset.reset': 'earliest',
        'security.protocol': 'ssl',
        'ssl.ca.location': SSL_CA_LOCATION,
        'ssl.certificate.location': SSL_CERT_LOCATION,
        'ssl.key.location': SSL_KEY_LOCATION,
        # Add other consumer settings here
    }
    return Consumer(consumer_config)