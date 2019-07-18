from abc import ABCMeta, abstractmethod, abstractproperty


class JobFailedException(Exception):
    """For some reason we could not complete the job"""


class BaseExtractor(metaclass=ABCMeta):
    cancelled = False

    def __init__(self, job, page):
        self.job = job
        self.page = page

    @abstractproperty
    def name(self):
        """Name of plugin"""

    @abstractproperty
    def matcher(self):
        """Regexp to match URL"""

    @abstractproperty
    def priority(self):
        """We will use the one with highest priority"""

    @abstractmethod
    async def extract(self, job):
        """Extract data from job"""

    def wait_for_user_input(self, reason):
        self.job.status = self.job.WAITING
        self.job.status_message = reason
        self.job.save()
