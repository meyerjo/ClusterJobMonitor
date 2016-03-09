import logging
import xml.etree.ElementTree as ET

from sshmonitor import JobManager


class FileBasedJobManager(JobManager):

    def __init__(self, jobfile):
        tree = ET.parse(jobfile)
        self.root = tree.getroot()

    def get_all_jobs(self, filteroptions=None):
        types = ['active', 'eligible', 'completed', 'blocked']
        ret = {}
        for t in types:
            ret[t] = self._load_class_from_xml(self.root, t, filteroptions)
        return ret


    def get_active_jobs(self):
        log = logging.getLogger(__name__)
        jobs = self._load_class_from_xml(self.root, 'active')
        return jobs


    def get_eligible_jobs(self):
        log = logging.getLogger(__name__)
        jobs = self._load_class_from_xml(self.root, 'eligible')
        return jobs

    def get_completed_jobs(self):
        log = logging.getLogger(__name__)
        jobs = self._load_class_from_xml(self.root, 'completed')
        return jobs

    def get_blocked_jobs(self):
        log = logging.getLogger(__name__)
        jobs = self._load_class_from_xml(self.root, 'blocked')
        return jobs

    def cancel_job(self, jobid):
        assert(isinstance(jobid, int))
        log = logging.getLogger(__name__)
        log.error("Can't cancel job because file based mode is enabled")
        return dict(error="Can't cancel job, because no session is available")

    def submit_job(self, job):
        log = logging.getLogger(__name__)
        log.error("Can't subbmit jobs because no session is available")
        return dict(error='check log')

    def get_job_details(self, jobid):
        assert(isinstance(jobid, int))
        log = logging.getLogger(__name__)
        log.error("Can't retrieve additional text information")
        return dict(error='Check log')
