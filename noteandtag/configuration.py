DEFAULT_LOGGING_MAXBYTES = 1000000
DEFAULT_LOGGING_BACKUPCOUNT = 5
DEFAULT_CONFIG = {
    "service": {
        "port": 8080,
        "base-url": "/",
        "api-base-url": "/api/v1/",
        "swagger-url": "/api/v1/doc",
        "cdn-url": "",
        "db": "notes.yml"
    },
    "logging": {
        "access-logfile": "",
        "access-maxbytes": DEFAULT_LOGGING_MAXBYTES,
        "access-backupcount": DEFAULT_LOGGING_BACKUPCOUNT,
        "error-logfile": "",
        "error-maxbytes": DEFAULT_LOGGING_MAXBYTES,
        "error-backupcount": DEFAULT_LOGGING_BACKUPCOUNT,
    }
}


def load(path):
    """Load the service configuration from file.

    Returns default parameters overriden by the ones in the configuration file.

    :param path: file to load
    :return: a dict containing loaded configuration
    """
    import configparser

    result = dict(DEFAULT_CONFIG)
    config = configparser.ConfigParser()
    config.read(path)
    for s in config.sections():
        result.setdefault(s, {}).update(config.items(s))

    return result
