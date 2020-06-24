import logging

import os

from utils.haversine import Haversine 
from middleware.rabbitmq import Queue, Queues
from middleware.log import config_log

LAT = 0
LONG = 1

REGION = 0
LAT_REGION = 1
LONG_REGION = 2

REGIONS_QUEUE_NAME = "regions"
SEND_QUEUE_NAME = "positive_by_region"
RECEIVE_QUEUE_NAME = "positive_locations"

LOG_FREQUENCY = 10000

class DistanceCalculator(object):
    def __init__(self, regions_queue, receive_queue, send_queues):
        self.regions_queue = regions_queue
        self.receive_queue = receive_queue
        self.send_queues = send_queues
        self.regions = {}
        self.log_counter = 0
        self.haversine = None

    def run(self):
        logging.info("Start consuming regions")
        self.regions_queue.consume(self._callback_regions)
        self.haversine = Haversine(self.regions)
        logging.info("Start consuming cases")
        self.receive_queue.consume(self._callback)
        logging.info("Sending EOM to queues")
        self.send_queues.send_eom()
        logging.info("Finish")

    def _callback_regions(self, ch, method, properties, body):
        decoded_body = body.decode('UTF-8')
        body_values = decoded_body.rstrip().split(",")
        
        region = body_values[REGION]
        lat = float(body_values[LAT_REGION])
        long = float(body_values[LONG_REGION])
        if region not in self.regions:
            self.regions[region] = { 'lat': lat, 'long': long }

    def _callback(self, ch, method, properties, body):
        decoded_body = body.decode('UTF-8')

        splitted_body = decoded_body.split(';')
        for element in splitted_body:
            body_values = element.split(",")
            self.log_counter += 1

            lat = float(body_values[LAT])
            long = float(body_values[LONG])
            
            region = self.haversine.calculate_location(lat, long)

            if self.log_counter % LOG_FREQUENCY == 0:
                logging.info("Received line [%d] Lat %s, Long %s", self.log_counter, lat, long)
            self.send_queues.send(region)

if __name__ == '__main__':

    rabbitmq_host = os.environ['HOST']
    filter_parser_workers = int(os.environ['FILTER_PARSER_WORKERS'])
    # distance_workers = int(os.environ['DISTANCE_WORKERS'])
    counter_by_region_workers = int(os.environ['COUNTER_BY_REGION_WORKERS'])

    worker_id = int(os.environ['SERVICE_ID'])
    config_log("DISTANCE CALCULATOR {}".format(worker_id))

    regions_queue = Queue("{}_{}".format(REGIONS_QUEUE_NAME, worker_id), rabbitmq_host)
    receive_queue = Queue("{}_{}".format(RECEIVE_QUEUE_NAME, worker_id), rabbitmq_host, filter_parser_workers)
    send_queues = Queues(SEND_QUEUE_NAME, rabbitmq_host, counter_by_region_workers)
    worker = DistanceCalculator(regions_queue, receive_queue, send_queues)

    logging.info("Worker created, started running")
    worker.run()
    logging.info("Worker finished, exiting")
