import logging
import os

from middleware.rabbitmq import Queue, Queues
from middleware.log import config_log

DATE = 0
LAT = 1
LONG = 2
CASE = 3

POSITIVE = 'positivi'
DECEASE = 'deceduti'

COUNTER_QUEUE_NAME = "cases"
COUNTER_DATE_QUEUE_NAME = "cases_by_date"
DISTANCE_NAME_QUEUE = "positive_locations"
RECEIVE_QUEUE_NAME = "raw_cases"

LOG_FREQUENCY = 10000

class FilterParser(object):
    def __init__(self, receive_queue, counter_queues, counter_by_date_queues, distance_queues):
        self.counter_queues = counter_queues
        self.receive_queue = receive_queue
        self.counter_by_date_queues = counter_by_date_queues
        self.distance_queues = distance_queues
        self.log_counter = 0

    def run(self):
        logging.info("Start consuming")
        self.receive_queue.consume(self._callback)
        logging.info("MESSAGES: {}".format(self.log_counter))
        logging.info("Sending EOM to queues")
        self.counter_queues.send_eom()
        self.counter_by_date_queues.send_eom()
        self.distance_queues.send_eom()
        logging.info("Finish")

    def _callback(self, ch, method, properties, body):
        decoded_body = body.decode('UTF-8')

        body_values = decoded_body.rstrip().split(";")

        counter_array = []
        counter_by_date_array = []
        distance_array = []

        for element in body_values:
            splitted = element.split(',')

            self.log_counter += 1

            date = splitted[DATE]
            
            case = splitted[CASE]

            lat = splitted[LAT]
            long = splitted[LONG]

            if self.log_counter % LOG_FREQUENCY == 0:
                logging.info("Received line [%d] Case %s", self.log_counter, element)
                logging.info(counter_array)
            
            counter_array.append(case)
            counter_by_date_array.append("{},{}".format(date, case))
            if case == POSITIVE:
                distance_array.append("{},{}".format(lat, long))

        self.counter_queues.send(';'.join(counter_array))
        self.counter_by_date_queues.send(';'.join(counter_by_date_array))
        if len(distance_array) > 0:
            self.distance_queues.send(';'.join(distance_array))

if __name__ == '__main__':

    rabbitmq_host = os.environ['HOST']
    filter_parser_workers = int(os.environ['FILTER_PARSER_WORKERS'])
    counter_workers = int(os.environ['COUNTER_WORKERS'])
    counter_by_date_workers = int(os.environ['COUNTER_WORKERS'])
    distance_workers = int(os.environ['DISTANCE_WORKERS'])

    worker_id = int(os.environ['SERVICE_ID'])
    config_log("FILTER PARSER {}".format(worker_id))
    counter_queues = Queues(COUNTER_QUEUE_NAME, rabbitmq_host, counter_workers)
    counter_by_date_queues = Queues(COUNTER_DATE_QUEUE_NAME, rabbitmq_host, counter_by_date_workers)
    distance_queues = Queues(DISTANCE_NAME_QUEUE, rabbitmq_host, distance_workers)
    receive_queue = Queue("{}_{}".format(RECEIVE_QUEUE_NAME, worker_id), rabbitmq_host)
    worker = FilterParser(receive_queue, counter_queues, counter_by_date_queues, distance_queues)

    logging.info("Worker created, started running")
    worker.run()
    logging.info("Worker finished, exiting")
