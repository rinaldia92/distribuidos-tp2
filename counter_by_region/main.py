import logging
import os
from middleware.rabbitmq import Queue
from middleware.log import config_log

SEND_QUEUE_NAME = "total_by_region"
RECEIVE_QUEUE_NAME = "positive_by_region"

LOG_FREQUENCY = 10000

class CounterByRegion(object):
    def __init__(self, receive_queue, send_queue):
        self.send_queue = send_queue
        self.receive_queue = receive_queue
        self.log_counter = 0
        self.counter = {}

    def run(self):
        logging.info("Start consuming")
        self.receive_queue.consume(self._callback)
        self._send()
        logging.info("Sending EOM to queues")
        self.send_queue.send_eom()
        logging.info("Finish")

    def _callback(self, ch, method, properties, body):
        region = body.decode('UTF-8')

        self.log_counter += 1
        self.counter[region] = self.counter.get(region, 0) + 1

        if self.log_counter % LOG_FREQUENCY == 0:
            logging.info("Received line [%d] Region %s", self.log_counter, region)
            self._send()
    
    def _send(self):
        for region, cases in self.counter.items():
            self.send_queue.send('{},{}'.format(region,cases))
        self.counter = {} 


if __name__ == '__main__':
    host = os.environ['HOST']

    worker_id = int(os.environ['SERVICE_ID'])
    config_log("COUNTER BY REGION {}".format(worker_id))
    distance_workers = int(os.environ['DISTANCE_WORKERS'])
    send_queue = Queue(SEND_QUEUE_NAME, host)
    receive_queue = Queue("{}_{}".format(RECEIVE_QUEUE_NAME, worker_id), host, distance_workers)
    worker = CounterByRegion(receive_queue, send_queue)

    logging.info("Worker created, started running")
    worker.run()
    logging.info("Worker finished, exiting")
