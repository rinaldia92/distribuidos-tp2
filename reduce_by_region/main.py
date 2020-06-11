import logging
import os
import json
from middleware.rabbitmq import Queue
from middleware.log import config_log

REGION = 0
POSITIVES = 1

SEND_QUEUE_NAME = "end"
RECEIVE_QUEUE_NAME = "total_by_region"

class ReducerRegions(object):
    def __init__(self, receive_queue, send_queue):
        self.send_queue = send_queue
        self.receive_queue = receive_queue
        self.total = {}

    def run(self):
        logging.info("Start consuming")
        self.receive_queue.consume(self._callback)
        three_regions = self._calculate_three_regions() 
        self.send_queue.send(json.dumps(three_regions))
        logging.info("Sending EOM to queues")
        self.send_queue.send_eom()
        logging.info("Finish")

    def _callback(self, ch, method, properties, body):
        decoded_body = body.decode('UTF-8')
        body_values = decoded_body.split(',')

        region = body_values[REGION]
        positives = int(body_values[POSITIVES])
        
        self.total[region] = self.total.get(region, 0) + positives

    def _calculate_three_regions(self):
        items = self.total.items();
        items_ordered = sorted(items, key=lambda c: c[1], reverse=True)
        return items_ordered[0:3]

if __name__ == '__main__':
    host = os.environ['HOST']

    worker_id = int(os.environ['SERVICE_ID'])
    counter_by_region_workers = int(os.environ['COUNTER_BY_REGION_WORKERS'])

    config_log("TOTAL BY REGION {}".format(worker_id))

    send_queue = Queue(SEND_QUEUE_NAME, host)
    receive_queue = Queue(RECEIVE_QUEUE_NAME, host, counter_by_region_workers)
    worker = ReducerRegions(receive_queue, send_queue)

    logging.info("Worker created, started running")
    worker.run()
    logging.info("Worker finished, exiting")
