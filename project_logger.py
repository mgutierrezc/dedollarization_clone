import logging

def get_logger(name):
    """
    Creates logger for all the files in the project

    input: file name
    output: logger object
    """
    log_format = '%(asctime)s  %(name)8s  %(levelname)5s  %(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format=log_format,
                        filemode='w')
    file_handler = logging.FileHandler('dedollarization.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger(name).addHandler(file_handler)
    return logging.getLogger(name)