import logging
import os
import json
from middleware.rabbitmq import Queue
from middleware.log import config_log

SEND_QUEUE_NAME = "end"
RECEIVE_QUEUE_NAME = "total_by_date"

DATE = 0
POSITIVES = 1
DECEASES = 2
class ReducerByDate(object):
    def __init__(self, receive_queue, send_queue):
        self.send_queue = send_queue
        self.receive_queue = receive_queue
        self.total = {}

    def run(self):
        logging.info("Start consuming")
        self.receive_queue.consume(self._callback)
        self.send_queue.send(json.dumps(self.total))
        logging.info("Sending EOM to queues")
        self.send_queue.send_eom()
        logging.info("Finish")

    def _callback(self, ch, method, properties, body):
        decoded_body = body.decode('UTF-8')
        body_values = decoded_body.split(',')
        date = body_values[DATE]
        positives = int(body_values[POSITIVES])
        deceases = int(body_values[DECEASES])

        if date not in self.total:
            self.total[date] = { 'positive_cases': 0, 'decease_cases': 0 }

        self.total[date]['positive_cases'] += positives
        self.total[date]['decease_cases'] += deceases
        ch.basic_ack(delivery_tag = method.delivery_tag)

if __name__ == '__main__':
    host = os.environ['HOST']

    worker_id = int(os.environ['SERVICE_ID'])
    counter_workers = int(os.environ['COUNTER_BY_DATE_WORKERS'])
    config_log("TOTAL BY DATE {}".format(worker_id))
    send_queue = Queue(SEND_QUEUE_NAME, host)
    receive_queue = Queue(RECEIVE_QUEUE_NAME, host, counter_workers)
    worker = ReducerByDate(receive_queue, send_queue)

    logging.info("Worker created, started running")
    worker.run()
    logging.info("Worker finished, exiting")
