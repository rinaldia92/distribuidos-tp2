import logging
import os
from middleware.rabbitmq import Queues
from middleware.log import config_log

FILE = './docs/italia_regioni.csv'

SEND_QUEUE_NAME = "regions"

class RegionReader(object):
    def __init__(self, file_path, rabbitmq_queues):
        self.file_path = file_path
        self.queues = rabbitmq_queues

    def start(self):
        region_number = 0
        with open(self.file_path, "r") as regions:
            next(regions) #skip headers
            
            for region in regions:
                self.queues.send_all(region)
                region_number += 1

        logging.info("Cases sended: {}".format(region_number))
        logging.info("Sending EOM")
        self.queues.send_eom()

if __name__ == '__main__':
    config_log("INIT REGIONS")

    rabbitmq_host = os.environ['HOST']
    distance_workers = int(os.environ['DISTANCE_WORKERS'])

    rabbitmq_queues = Queues(SEND_QUEUE_NAME, rabbitmq_host, distance_workers)

    worker = RegionReader(FILE, rabbitmq_queues)
    logging.info("Worker created, started running")
    worker.start()
    logging.info("Worker finished, exiting")