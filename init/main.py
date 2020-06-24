import logging
import os
import random
import sys
import time
from middleware.rabbitmq import Queues
from middleware.log import config_log

FILE = './docs/italia_nuovi_casi.csv'

SEND_QUEUE_NAME = "raw_cases"

LOG_FREQUENCY = 10000

class CasesReader(object):
    def __init__(self, file_path, rabbitmq_queues):
        self.file_path = file_path
        self.queues = rabbitmq_queues

    def start(self):
        case_number = 0
        cases_accum = []
        with open(self.file_path, "r") as cases:
            next(cases) #skip headers
            
            for case in cases:
                cases_accum.append(case)
                case_number += 1
                if (len(cases_accum) == 10):
                    self.queues.send(';'.join(cases_accum))    
                    cases_accum = []
                if (case_number % LOG_FREQUENCY == 0):
                    logging.info("Sending case [%d] %s", case_number, case)
                    time.sleep(5)
        if (len(cases_accum) > 0):
            self.queues.send(';'.join(cases_accum))           
        logging.info("Cases sended: {}".format(case_number))
        logging.info("Sending EOM")
        self.queues.send_eom()

if __name__ == '__main__':
    config_log("INIT")

    rabbitmq_host = os.environ['HOST']
    filter_parser_workers = int(os.environ['FILTER_PARSER_WORKERS'])

    rabbitmq_queues = Queues(SEND_QUEUE_NAME, rabbitmq_host, filter_parser_workers)
    worker = CasesReader(FILE, rabbitmq_queues)
    logging.info("Worker created, started running")
    worker.start()
    logging.info("Worker finished, exiting")