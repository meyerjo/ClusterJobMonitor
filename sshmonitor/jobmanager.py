import logging
import xml.etree.ElementTree as ET

import re

import datetime


class JobManager:

    def filter_from_dict(self, input_dict, filteroptions=None):
        assert(isinstance(input_dict, dict))
        if filteroptions is None:
            return input_dict
        assert(isinstance(filteroptions, list))
        for (key, val) in input_dict.items():
            if val is []:
                continue
            for i, r in enumerate(val):
                if not isinstance(r, dict):
                    log = logging.getLogger(__name__)
                    log.warning('Element is not a dict and it should be one')
                    log.warning(val)
                    continue
                available_keys = r.keys()
                keys_to_delete = [x for x in available_keys if x not in filteroptions]
                if r is None:
                    continue
                for f in keys_to_delete:
                    del input_dict[key][i][f]
        return input_dict

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
        assert(isinstance(listdict, dict))
        log = logging.getLogger(__name__)
        updated_result = {}
        for (classkey, classmembers) in listdict.items():
            if re.search('^error', classkey):
                log.info('Skipping classkey {0}, because it matches the regex \'^error\''.format(classkey))
                updated_result[classkey] = classmembers
                continue

            if len(classmembers) > 0:
                keyname_list = list(classmembers[0].keys())
                ids = [filteroptions.index(x) for x in keyname_list]
                sorted_keys = [line for (id, line) in sorted(zip(ids, keyname_list))]
                header = sorted_keys
                body = []
                for row in classmembers:
                    keyname_list = list(row.keys())
                    ids = [filteroptions.index(x) for x in keyname_list]

                    row_values = row.values()
                    sorted_values = [line for (id, line) in sorted(zip(ids, row_values))]
                    body.append(sorted_values)
                updated_result[classkey] = dict(header=header, body=body)
            else:
                updated_result[classkey] = dict(header=[], body=[])
        return updated_result

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