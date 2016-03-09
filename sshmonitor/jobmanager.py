import logging
import xml.etree.ElementTree as ET

import re

import datetime


class JobManager:

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

    def _load_class_from_xml(self, xmltree_root, option, filteroptions=None):
        ret = []
        for child in xmltree_root.findall('queue'):
            if 'option' not in child.attrib:
                continue
            if child.attrib['option'] == option:
                for element in child:
                    a = self._filter_from_dict(element.attrib, filteroptions)
                    a = self._preprocess_data(a)
                    ret.append(a)
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
