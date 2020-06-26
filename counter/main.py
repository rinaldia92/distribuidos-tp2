import logging

import os

from middleware.rabbitmq import Queue
from middleware.log import config_log

NUM_COLUMS = 2

POSITIVE = 'positivi'
DECEASE = 'deceduti'

SEND_QUEUE_NAME = "percentage"
RECEIVE_QUEUE_NAME = "cases"

LOG_FREQUENCY = 10000
class CounterCases(object):
    def __init__(self, receive_queue, send_queue):
        self.send_queue = send_queue
        self.receive_queue = receive_queue
        self.log_counter = 0
        self.positive_cases = 0
        self.decease_cases = 0

    def run(self):
        logging.info("Start consuming")
        self.receive_queue.consume(self._callback)
        self.send_queue.send('{},{}'.format(self.positive_cases, self.decease_cases))
        logging.info("Sending EOM to queue")
        self.send_queue.send_eom()
        logging.info("Finish")

    def _callback(self, ch, method, properties, body):
        decoded_body = body.decode('UTF-8')

        splitted_body = decoded_body.split(';')

        for element in splitted_body:
            if element == POSITIVE:
                self.positive_cases += 1
            elif element == DECEASE:
                self.decease_cases += 1
            else:
                return
            
            self.log_counter += 1

            if self.log_counter % LOG_FREQUENCY == 0:
                logging.info("Received line [%d] Case %s", self.log_counter, element)
                logging.info("Sending %d,%d", self.positive_cases, self.decease_cases)
                self.send_queue.send('{},{}'.format(self.positive_cases, self.decease_cases))        
                self.positive_cases = 0
                self.decease_cases = 0
        ch.basic_ack(delivery_tag = method.delivery_tag)

if __name__ == '__main__':
    host = os.environ['HOST']
    filter_workers = int(os.environ['FILTER_PARSER_WORKERS'])
    worker_id = int(os.environ['SERVICE_ID'])

    config_log("COUNTER {}".format(worker_id))

    send_queue = Queue(SEND_QUEUE_NAME, host)
    receive_queue = Queue("{}_{}".format(RECEIVE_QUEUE_NAME, worker_id), host, filter_workers)
    worker = CounterCases(receive_queue, send_queue)

    logging.info("Worker created, started running")
    worker.run()
    logging.info("Worker finished, exiting")
