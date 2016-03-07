import logging
import xml.etree.ElementTree as ET

import re

import datetime


class JobManager():

    def __init__(self, jobfile):
        tree = ET.parse(jobfile)
        self.root = tree.getroot()
        self.session = None

    def _filter_from_dict(self, input_dict, filteroptions=None):
        if filteroptions is None:
            return input_dict
        else:
            available_keys = input_dict.keys()
            keys_to_delete = [x for x in available_keys if x not in filteroptions]
            if input_dict is None:
                return input_dict
            for f in keys_to_delete:
                del input_dict[f]
            return input_dict

    def _preprocess_data(self, input_dict):
        for (item, key) in input_dict.items():
            if re.search('Time$', item) is not None:
                # preprocess data
                timestamp = int(key)
                input_dict[item] = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        return input_dict

    def _load_class_from_xml(self, option, filteroptions=None):
        ret = []
        for child in self.root.findall('queue'):
            if 'option' not in child.attrib:
                continue
            if child.attrib['option'] == option:
                for element in child:
                    a = self._filter_from_dict(element.attrib, filteroptions)
                    a = self._preprocess_data(a)
                    ret.append(a)
        return ret

    def get_all_jobs(self, filteroptions=None):
        types = ['active', 'eligible', 'completed', 'blocked']
        ret = {}
        for t in types:
            ret[t] = self._load_class_from_xml(t, filteroptions)
        return ret


    def get_active_jobs(self):
        log = logging.getLogger(__name__)
        jobs = self._load_class_from_xml('active')
        return jobs


    def get_eligible_jobs(self):
        log = logging.getLogger(__name__)
        jobs = self._load_class_from_xml('eligible')
        return jobs

    def get_completed_jobs(self):
        log = logging.getLogger(__name__)
        jobs = self._load_class_from_xml('completed')
        return jobs

    def get_blocked_jobs(self):
        log = logging.getLogger(__name__)
        jobs = self._load_class_from_xml('blocked')
        return jobs

    def cancel_job(self, jobid):
        assert(isinstance(jobid, int))
        log = logging.getLogger(__name__)
        if self.session is None:
            log.error("Can't cancel job because no session is available")
            return dict(error="Can't cancel job, because no session is available")
        else:
            cmd = 'mjobctl -c {0}'.format(jobid)
            log.error('Not yet implemented. Send "{0}" to the server'.format(cmd))
            return dict(error='Not yet implemented')

    def submit_job(self, job):
        log = logging.getLogger(__name__)
        log.error('Not yet implemented {0}'.format(job))

    def get_job_details(self, jobid):
        assert(isinstance(jobid, int))
