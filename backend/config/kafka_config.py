from django.conf import settings


def build_kafka_config(extra: dict | None = None) -> dict:
    config = {
        'bootstrap.servers': settings.KAFKA_BROKER,
    }

    if settings.KAFKA_SECURITY_PROTOCOL != 'PLAINTEXT':
        config['security.protocol'] = settings.KAFKA_SECURITY_PROTOCOL
        config['sasl.mechanism'] = settings.KAFKA_SASL_MECHANISM
        config['sasl.username'] = settings.KAFKA_SASL_USERNAME
        config['sasl.password'] = settings.KAFKA_SASL_PASSWORD

    if settings.KAFKA_SSL_CA_LOCATION:
        config['ssl.ca.location'] = settings.KAFKA_SSL_CA_LOCATION

    if extra:
        config.update(extra)

    return config
