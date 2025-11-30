import threading
import pika, sys, os

def start_event_subscriber():
    """Start RabbitMQ event subscriber in a separate thread"""
    def subscriber():
        while True:
            try:
                rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
                rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
                rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
                rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')
                
                credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
                parameters = pika.ConnectionParameters(
                    host=rabbitmq_host,
                    port=rabbitmq_port,
                    credentials=credentials
                )
                
                connection = pika.BlockingConnection(parameters)
                channel = connection.channel()

                
                # Create queue for order service
                result = channel.queue_declare(queue='hello')
                queue_name = result.method.queue
                
                
                print("✓ Order service subscribed to user events")
                
                def callback(ch, method, properties, body):
                    try:
                        print(f" [x] Received {method.routing_key} : {body.decode()}")
                        # Here you would add logic to handle the event, e.g., update orders
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        print(f"Error processing event: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
                channel.basic_consume(queue=queue_name, on_message_callback=callback)
                
                print("✓ Waiting for user events...")
                channel.start_consuming()
                
            except Exception as e:
                print(f"RabbitMQ subscriber error: {e}")
                print("Retrying in 5 seconds...")
                import time
                time.sleep(5)
    
    #need thread to run in background because start_consuming() is ALWAYSblocking
    thread = threading.Thread(target=subscriber, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    try:
        start_event_subscriber()
        # Keep the main thread alive to allow the subscriber to run
        while True:
            pass 
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)