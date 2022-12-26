
"""
utility functions to establish logging functionality
"""

import logging
import yaml
from timer import Timer


def log_machine(f):
    """
    decorator function to add logging capability
    usage : add @log_machine to functions for which logging is requested
    logs start time and completion time and time to execute each decorated function
    assumes : log file and logger previously initiated by setup_logger()
    :param f: wrapped (decorated) function
    :return: result of wrapper function
    """

    def wrapper(*args, **kwargs):
        """
        executes the logging mechanism at entry and exit of decorated function
        :param args: args supplied to wrapped function
        :param kwargs: kwargs supplied to wrapped function
        :return: returned objs from wrapped function
        """

        # start the timer
        t = Timer()
        t.start()

        # start message to log file
        logger = logging.getLogger(__name__)
        log_message = ('%s | start |' % f.__name__)
        logger.info(log_message)

        # execute the called function
        returned_objs = f(*args, **kwargs)

        # stop the timer, log exit
        log_message = ('%s | complete | %.2f' % (f.__name__, t.stop()))
        logger.info(log_message)

        # return control to calling function
        return returned_objs

    return wrapper


@log_machine
def read_config(file_path):
    """
    :param file_path:
    :return: cfg, loaded yaml file
    """
    with open(file_path, "r") as f:
        cfg = yaml.safe_load(f)

    return cfg


def setup_this_run(sys_args):
    """
    initiate config dict which provides run control parameter settings
    some default setting are defined
    config file name 'config.yaml' from main directory is read (if available) and overwerites defaults
    finally, if sys.argv had command line definition of input directory, that overwrites any previously stored string

    :param sys_args: command line sys.argv list
    :return: config: dict - k,v pairs of run config parameters
    """

    # some default config settings :

    config = {}

    # if available, overwrite defaults with config.yaml file settings
    try:
        config_yml = read_config("config.yaml")

        for ykey in config_yml:
            config[ykey] = config_yml[ykey]

    except FileNotFoundError as fnfe:
        print('config.yaml file not found - aborting execution')
        exit(-1)

    # retain base capability to define input path as command line argument
    if len(sys_args) > 1:
        config['input'] = sys_args[1]

    return config


def setup_logger(sys_args: list, config: dict) -> logging.getLoggerClass():
    """
    initiate logger for main routine
    all hard coded options at the moment
    :return: logger object
    """

    log_format = "%(levelname)s | %(asctime)s | %(name)s | %(message)s"

    log_filename = sys_args[0].strip('.py') + '.log'

    logging.basicConfig(format=log_format,
                        level=logging.INFO,
                        handlers=[
                            logging.FileHandler(log_filename),
                            logging.StreamHandler()]
                        )
    logger = logging.getLogger()

    try:
        if 'logging_level' in config:
            log_level = logging.getLevelName(config['logging_level'])
            logger.setLevel(log_level)
    except ValueError as ve:
        logger.critical('ValueError in setting log level from config file : ' + str(ve))

    return logger
