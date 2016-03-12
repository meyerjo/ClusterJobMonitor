import logging
import xml

import datetime
import paramiko
import re

from sshmonitor import JobManager
import xml.etree.ElementTree as ET

from sshmonitor.ssh_connectionholder import SSHConnectionHolder


class SSHBasedJobManager(JobManager):

    def __init__(self, ssh):
        # establish ssh connection
        assert(isinstance(ssh, SSHConnectionHolder))
        log = logging.getLogger(__name__)
        self.ssh = ssh

    def _send_showq_request(self, command):
        log = logging.getLogger(__name__)
        log.debug('Querying jobs {0}'.format(command))
        return_dict = self.ssh.send_command(command)
        if return_dict['error'] is None:
            lines = return_dict['stdoutstr']
            tree = ET.fromstring(lines)
            return tree
        return return_dict

    def _from_basic_showq(self, classname, filteroptions=None):
        log = logging.getLogger(__name__)
        log.debug('Querying {0} jobs'.format(classname))
        cmd = 'showq --xml'
        retobj = self._send_showq_request(cmd)
        if isinstance(retobj, xml.etree.ElementTree.Element):
            return self._load_class_from_xml(retobj, classname, filteroptions)
        return retobj

    def get_active_jobs(self, filteroptions=None):
        return self._from_basic_showq('active', filteroptions)

    def get_blocked_jobs(self, filteroptions=None):
        return self._from_basic_showq('blocked', filteroptions)

    def get_all_jobs(self, filteroptions=None):
        types = ['active', 'eligible', 'blocked']
        ret = {}
        for t in types:
            ret[t] = self._from_basic_showq(t, filteroptions)

        ret['completed'] = self.get_completed_jobs(filteroptions)
        return ret

    def get_eligible_jobs(self, filteroptions=None):
        return self._from_basic_showq('eligible', filteroptions)

    def get_completed_jobs(self, filteroptions=None):
        log = logging.getLogger(__name__)
        log.debug('Querying {0} jobs'.format('completed'))
        tree = self._send_showq_request('showq --xml -c')
        if isinstance(tree, xml.etree.ElementTree.Element):
            return self._load_class_from_xml(tree, 'completed', filteroptions)
        return tree

    def get_job_details(self, jobid):
        cmd = 'checkjob --xml {0}'.format(jobid)
        log = logging.getLogger(__name__)
        log.debug('Checking job details for {0}'.format(jobid))
        output = self.ssh.send_command(cmd)
        if output['error'] is None:
            lines = output['stdoutstr']
            xml_output = ET.fromstring(lines)
            jobs = xml_output.findall('job')
            outputattribs = None
            if len(jobs) == 1:
                req_node = jobs[0].findall('req')
                outputattribs = jobs[0].attrib
                if len(req_node) == 1:
                    outputattribs.update(req_node[0].attrib)
                for (key, vals) in outputattribs.items():
                    if re.search('Time$', key) and re.search('[0-9]*', vals):
                        outputattribs[key] = '{0} ({1})'.format(vals,
                                                                datetime.datetime.fromtimestamp(int(vals)).strftime('%Y-%m-%d %H:%M:%S'))
            output = outputattribs
        else:
            output = output['error']
        return output

    def submit_job(self, job):
        log = logging.getLogger(__name__)
        log.error('not yet implemented')
        pass

    def cancel_job(self, jobid):
        log = logging.getLogger(__name__)
        log.info('Cancel job with id: {0}'.format(jobid))
        cmd = 'mjobctl -c {0}'.format(jobid)
        ret = self.ssh.send_command(cmd)
        return ret



