import logging
import os
from middleware.rabbitmq import Queue
from middleware.log import config_log

NUM_COLUMS = 2

POSITIVE = 'positivi'
DECEASE = 'deceduti'

SEND_QUEUE_NAME = "total_by_date"
RECEIVE_QUEUE_NAME = "cases_by_date"

LOG_FREQUENCY = 10000


class CounterCases(object):
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
        decoded_body = body.decode('UTF-8')

        splitted_body = decoded_body.split(';')
        
        for element in splitted_body:
            splitted_element = element.split(',')
            date = splitted_element[0]
            date = date.split()[0]
            case = splitted_element[1]

            self.log_counter += 1
        
            if date not in self.counter:
                self.counter[date] = { 'positive_cases': 0, 'decease_cases': 0 }

            if case == POSITIVE:
                self.counter[date]['positive_cases'] += 1
            elif case == DECEASE:
                self.counter[date]['decease_cases'] += 1
            else:
                return
            
            if self.log_counter % LOG_FREQUENCY == 0:
                logging.info("Received line [%d] Date %s Case %s", self.log_counter, date, case)
                self._send()

    def _send(self):
        for date, cases in self.counter.items():
            self.send_queue.send('{},{},{}'.format(date, cases['positive_cases'], cases['decease_cases']))
        self.counter = {}

if __name__ == '__main__':
    host = os.environ['HOST']

    worker_id = int(os.environ['SERVICE_ID'])
    config_log("COUNTER BY DATE {}".format(worker_id))
    filter_workers = int(os.environ['FILTER_PARSER_WORKERS'])
    send_queue = Queue(SEND_QUEUE_NAME, host)
    receive_queue = Queue("{}_{}".format(RECEIVE_QUEUE_NAME, worker_id), host, filter_workers)
    worker = CounterCases(receive_queue, send_queue)

    logging.info("Worker created, started running")
    worker.run()
    logging.info("Worker finished, exiting")
