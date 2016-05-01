import logging
import xml.etree.ElementTree as ET

import re

import datetime

from sshmonitor.filter_data import filter_elements_from_dict, convert_list_of_dicts_to_list


class JobManager:

    def filter_from_dict(self, input_dict, filteroptions=None):
        return filter_elements_from_dict(input_dict, filteroptions)

    def _preprocess_data(self, input_dict):
        assert(isinstance(input_dict, dict))
        for (key, item) in input_dict.items():
            if re.search('Time$', key) and re.search('[0-9]*', item):
                # preprocess data
                timestamp = int(item)
                str_timestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                input_dict[key] = str_timestamp
        return input_dict

    def convert_from_listdict_to_list(self, listdict, filteroptions):
        return convert_list_of_dicts_to_list(listdict, filteroptions)

    def _load_class_from_xml(self, xmltree_root, option, filteroptions=None):
        ret = []
        for child in xmltree_root.findall('queue'):
            if 'option' not in child.attrib:
                continue
            if child.attrib['option'] == option:
                for element in child:
                    element = self._preprocess_data(element.attrib)
                    ret.append(element)
        return ret

    def get_all_jobs(self, filteroptions=None):
        pass

    def get_active_jobs(self):
        pass


    def get_eligible_jobs(self):
        pass

    def get_completed_jobs(self):
        pass

    def get_blocked_jobs(self):
        pass

    def cancel_job(self, jobid):
        pass

    def submit_job(self, job):
        pass

    def get_job_details(self, jobid):
        pass

    def get_job_output(self, jobid):
        pass