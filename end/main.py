import logging
import os
import random
import sys
from middleware.rabbitmq import Queue
from middleware.log import config_log

FILE = './docs/results'

RECEIVE_QUEUE_NAME = "end"

# LOG_FREQUENCY = 1000

class End(object):
    def __init__(self, file_path, rabbitmq_queue):
        self.file_path = file_path
        self.queue = rabbitmq_queue


    def run(self):
        logging.info("Start consuming")
        self.queue.consume(self._callback)
        logging.info("Finish")

    def _callback(self, ch, method, properties, body):
        decoded_body = body.decode('UTF-8')
        
        with open(self.file_path, "a") as file:
            file.write(decoded_body)
            file.write('\n')

if __name__ == '__main__':
    config_log("END")

    rabbitmq_host = os.environ['HOST']
    reducer_workers = int(os.environ['REDUCER_WORKERS'])

    rabbitmq_queue = Queue(RECEIVE_QUEUE_NAME, rabbitmq_host, reducer_workers)

    reporter = End(FILE, rabbitmq_queue)
    logging.info("Worker created, started running")
    reporter.run()
    logging.info("Worker finished, exiting")