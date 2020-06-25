import pika

EOM = "None"

class Queue(object):
    def __init__(self, queue_name, host, producers = 1):
        self.connection_host = host
        self.queue = queue_name
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.connection_host, heartbeat=10000, blocked_connection_timeout=300))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=True, arguments={ "max-length-bytes": 10485760, "max-length": 200000 })
        # self.channel.queue_declare(queue=self.queue, durable=True, arguments={ "max-length": 100000 })
        self.channel.basic_qos(prefetch_count=1)
        self.producers = producers
        self.tag = None

    def send(self, msg):
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=msg, properties=pika.BasicProperties(delivery_mode = 2,))

    def send_eom(self):
        self.send(EOM)

    def consume(self, callback):
        def _wrapper(ch, method, properties, body):
            if body.decode('UTF-8') == EOM:
                self.producers -= 1
                if self.producers == 0:
                    self._stop_consume()
                return
            callback(ch,method,properties,body)

        self.tag = self.channel.basic_consume(queue=self.queue, auto_ack=True, on_message_callback=_wrapper)
        self.channel.start_consuming()

    def _stop_consume(self):
        self.channel.basic_cancel(self.tag)

    def __exit__(self, *args):
        self.connection.close()

class Queues(object):
    def __init__(self, queue_name, host, number_of_queues, producers = None):
        self.queue = queue_name
        self.queues = []
        for i in range(number_of_queues):
            queue = Queue("{}_{}".format(queue_name, i+1), host, producers)
            self.queues.append(queue)
        self.message_count = 0

    def send(self, msg):
        queue = self.queues[self.message_count % len(self.queues)]
        queue.send(msg)
        self.message_count += 1
    
    def send_all(self, msg):
        for queue in self.queues:
            queue.send(msg)

    def send_eom(self):
        for queue in self.queues:
            queue.send_eom()
