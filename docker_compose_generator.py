import os

def generate_config_file(name, args, id = 1):
    with open('config/{}'.format(name), 'w') as config_file:
        config_file.write('HOST=rabbitmq\n')
        config_file.write('SERVICE_ID={}\n'.format(id))
        config_file.write('FILTER_PARSER_WORKERS={}\n'.format(args['filter_parser_workers']))
        config_file.write('COUNTER_WORKERS={}\n'.format(args['counter_workers']))
        config_file.write('COUNTER_BY_DATE_WORKERS={}\n'.format(args['counter_by_date_workers']))
        config_file.write('COUNTER_BY_REGION_WORKERS={}\n'.format(args['counter_by_region_workers']))
        config_file.write('DISTANCE_WORKERS={}\n'.format(args['distance_workers']))
        config_file.write('REDUCER_WORKERS={}\n'.format(args['reducer_workers']))
        config_file.write('LOGS_FILE=/docs/logs\n')

def write_header(file):
    file.write('version: \'2.1\'\nservices:\n')

def write_rabbit_service(file):
    file.write('  rabbitmq:\n')
    file.write('    image: rabbitmq-healthy\n')
    file.write('    ports:\n')
    file.write('      - 15672:15672\n')
    file.write('      - 5672:5672\n')
    file.write('    healthcheck:\n')
    file.write('      test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:15672\"]\n')
    file.write('      interval: 30s\n')
    file.write('      timeout: 10s\n')
    file.write('      retries: 5\n')
    file.write('\n')

def write_unique_service(file, image_name, config_name, args, end = False):
    generate_config_file('{}_config.env'.format(config_name), args)
    file.write("  {}:\n".format(image_name))
    file.write('    container_name: {}\n'.format(image_name))
    file.write('    image: {}:latest\n'.format(image_name))
    file.write('    env_file:\n')
    file.write('      - config/{}_config.env\n'.format(config_name))
    file.write('    entrypoint: python3 /main.py\n')
    file.write('    volumes:\n')
    file.write('      - ./docs:/docs\n')
    file.write('    links:\n')
    file.write('      - rabbitmq\n')
    file.write('    depends_on:\n')
    if not end:
        file.write('      rabbitmq:\n')
        file.write('        condition: service_healthy\n')
    else:
        for i in range(args['filter_parser_workers']):
            file.write('      - filter-parser-{}\n'.format(i+1))  
        for i in range(args['counter_workers']):
            file.write('      - counter-{}\n'.format(i+1))
        for i in range(args['counter_by_date_workers']):
            file.write('      - counter-by-date-{}\n'.format(i+1))
        for i in range(args['distance_workers']):
            file.write('      - distance-{}\n'.format(i+1))
    file.write('\n')

def write_worker_service(file, image_name, config_name, id, args):
    generate_config_file('{}_config_{}.env'.format(config_name, id), args, id)
    file.write("  {}-{}:\n".format(image_name, id))
    file.write('    container_name: {}-{}\n'.format(image_name, id))
    file.write('    image: {}:latest\n'.format(image_name))
    file.write('    env_file:\n')
    file.write('      - config/{}_config_{}.env\n'.format(config_name, id))
    file.write('    entrypoint: python3 /main.py\n')
    file.write('    volumes:\n')
    file.write('      - ./docs:/docs\n')
    file.write('    links:\n')
    file.write('      - rabbitmq\n')
    file.write('    depends_on:\n')
    file.write('      rabbitmq:\n')
    file.write('        condition: service_healthy\n')
    file.write('\n')

def generate_docker_compose_file(args):   
    if not os.path.exists('config'):
        os.mkdir('config')
    with open("docker-compose.yaml", "w") as docker_compose_file:
        write_header(docker_compose_file)
        write_rabbit_service(docker_compose_file)

        write_unique_service(docker_compose_file, 'init', 'init', args, True)

        for i in range(args['filter_parser_workers']):
            write_worker_service(docker_compose_file, 'filter-parser', 'filter_parser', i+1, args)

        for i in range(args['counter_workers']):
            write_worker_service(docker_compose_file, 'counter', 'counter', i+1, args)

        write_unique_service(docker_compose_file, 'percentage', 'reduce_percentage', args)

        for i in range(args['counter_by_date_workers']):
            write_worker_service(docker_compose_file, 'counter-by-date', 'counter_by_date', i+1, args)

        write_unique_service(docker_compose_file, 'total-by-date', 'reduce_by_date', args)

        write_unique_service(docker_compose_file, 'init-regions', 'init_regions', args)

        for i in range(args['distance_workers']):
            write_worker_service(docker_compose_file, 'distance', 'distance', i+1, args)

        for i in range(args['counter_by_region_workers']):
            write_worker_service(docker_compose_file, 'counter-by-region', 'counter_by_region', i+1, args)

        write_unique_service(docker_compose_file, 'total-by-region', 'reduce_by_region', args)

        write_unique_service(docker_compose_file, 'end', 'end', args)


if __name__ == '__main__':
    workers = {
        'filter_parser_workers': 1,
        'counter_workers': 1,
        'counter_by_date_workers': 1,
        'counter_by_region_workers': 1,
        'distance_workers': 2,
        'reducer_workers': 3 
    }

    generate_docker_compose_file(workers)