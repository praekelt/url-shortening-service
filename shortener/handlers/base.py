class BaseApiHandler(object):
    def __init__(self, config, db_engine):
        self.config = config
        self.engine = db_engine

    def render(self):
        """
        Generates a dict that will be returned as json

        Should return a Dict
        """
        raise NotImplementedError('Subclasses should implement this.')
