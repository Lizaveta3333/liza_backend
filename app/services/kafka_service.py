import json
import logging
from typing import Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable
import os
from threading import Thread

logger = logging.getLogger(__name__)

# Kafka configuration from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC_ORDERS = os.getenv("KAFKA_TOPIC_ORDERS", "order-events")

# Global producer instance
_producer: Optional[KafkaProducer] = None
_consumer: Optional[KafkaConsumer] = None
_consumer_thread: Optional[Thread] = None


def get_producer() -> Optional[KafkaProducer]:
    """Get or create Kafka producer instance"""
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            logger.info(f"Kafka producer initialized with servers: {KAFKA_BOOTSTRAP_SERVERS}")
        except NoBrokersAvailable:
            logger.warning(f"Kafka brokers not available at {KAFKA_BOOTSTRAP_SERVERS}. Producer will not be available. This is OK if Kafka is not running.")
            _producer = None
        except Exception as e:
            logger.warning(f"Failed to initialize Kafka producer: {e}. Producer will not be available.")
            _producer = None
    return _producer


def send_order_event(event_type: str, order_data: dict):
    """Send order event to Kafka topic"""
    producer = get_producer()
    if producer is None:
        logger.warning("Kafka producer not available, skipping event")
        return
    
    try:
        event = {
            "event_type": event_type,
            "order_id": order_data.get("id"),
            "buyer_id": order_data.get("buyer_id"),
            "product_id": order_data.get("product_id"),
            "quantity": order_data.get("quantity"),
            "status": order_data.get("status"),
            "timestamp": order_data.get("created_at", ""),
        }
        
        producer.send(
            KAFKA_TOPIC_ORDERS,
            key=str(order_data.get("id", "")),
            value=event
        )
        producer.flush()
        logger.info(f"Sent {event_type} event for order {order_data.get('id')} to Kafka")
    except KafkaError as e:
        logger.error(f"Failed to send event to Kafka: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending event to Kafka: {e}")


def _consume_messages():
    """Background thread function to consume Kafka messages"""
    global _consumer
    try:
        _consumer = KafkaConsumer(
            KAFKA_TOPIC_ORDERS,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='liza-order-processor'
        )
        logger.info(f"Kafka consumer started, listening to topic: {KAFKA_TOPIC_ORDERS}")
        
        for message in _consumer:
            try:
                event = message.value
                logger.info(f"Received Kafka event: {event.get('event_type')} for order {event.get('order_id')}")
                # Here you could add more processing logic if needed
            except Exception as e:
                logger.error(f"Error processing Kafka message: {e}")
    except NoBrokersAvailable:
        logger.warning(f"Kafka brokers not available at {KAFKA_BOOTSTRAP_SERVERS}. Consumer will not start. This is OK if Kafka is not running.")
        _consumer = None
    except Exception as e:
        logger.warning(f"Failed to start Kafka consumer: {e}. Consumer will not start.")
        _consumer = None


def start_consumer():
    """Start Kafka consumer in background thread"""
    global _consumer_thread
    if _consumer_thread is None or not _consumer_thread.is_alive():
        try:
            _consumer_thread = Thread(target=_consume_messages, daemon=True)
            _consumer_thread.start()
            logger.info("Kafka consumer thread started")
        except Exception as e:
            logger.error(f"Failed to start consumer thread: {e}")


def close_producer():
    """Close Kafka producer"""
    global _producer
    if _producer:
        try:
            _producer.close()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing producer: {e}")
        finally:
            _producer = None


def close_consumer():
    """Close Kafka consumer"""
    global _consumer
    if _consumer:
        try:
            _consumer.close()
            logger.info("Kafka consumer closed")
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")
        finally:
            _consumer = None


def get_kafka_status() -> dict:
    """Get Kafka connection status"""
    producer = get_producer()
    producer_available = producer is not None
    
    # Try to send a test message if producer is available
    test_sent = False
    if producer_available:
        try:
            test_event = {
                "event_type": "test",
                "order_id": None,
                "buyer_id": None,
                "product_id": None,
                "quantity": 0,
                "status": "test",
                "timestamp": "",
            }
            producer.send(KAFKA_TOPIC_ORDERS, key="test", value=test_event)
            producer.flush()
            test_sent = True
        except Exception as e:
            logger.error(f"Failed to send test message: {e}")
    
    return {
        "kafka_configured": True,
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "topic": KAFKA_TOPIC_ORDERS,
        "producer_available": producer_available,
        "consumer_running": _consumer is not None,
        "test_message_sent": test_sent,
    }

