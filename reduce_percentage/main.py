import logging
import os

from middleware.rabbitmq import Queue
from middleware.log import config_log

NUM_COLUMS = 2

POSITIVE = 0
DECEASE = 1

SEND_QUEUE_NAME = "end"
RECEIVE_QUEUE_NAME = "percentage"

class ReducerPercentage(object):
    def __init__(self, receive_queue, send_queue):
        self.send_queue = send_queue
        self.receive_queue = receive_queue
        self.log_counter = 0
        self.positive_cases = 0
        self.decease_cases = 0

    def run(self):
        logging.info("Start consuming")
        self.receive_queue.consume(self._callback)

        percentage = self.decease_cases / self.positive_cases

        logging.info('Positive cases: {}'.format(self.positive_cases))
        logging.info('Decease cases: {}'.format(self.decease_cases))
        self.send_queue.send("Percentage: {}".format(percentage))

        logging.info("Sending EOM to queues")
        self.send_queue.send_eom()
        logging.info("Finish")


    def _callback(self, ch, method, properties, body):
        decoded_body = body.decode('UTF-8')

        positives, deceases = decoded_body.split(',')

        self.positive_cases += int(positives)
        self.decease_cases += int(deceases)

        self.log_counter += 1


if __name__ == '__main__':
    host = os.environ['HOST']

    worker_id = int(os.environ['SERVICE_ID'])
    counter_workers = int(os.environ['COUNTER_WORKERS'])
    config_log("PERCENTAGE")
    send_queue = Queue(SEND_QUEUE_NAME, host)
    receive_queue = Queue(RECEIVE_QUEUE_NAME, host, counter_workers)
    worker = ReducerPercentage(receive_queue, send_queue)

    logging.info("Worker created, started running")
    worker.run()
    logging.info("Worker finished, exiting")
