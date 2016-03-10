import logging
import xml

import paramiko

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
            # process data
            print(output.items())
        return output

        pass

    def submit_job(self, job):
        pass

    def cancel_job(self, jobid):
        log = logging.getLogger(__name__)
        log.info('Cancel job with id: {0}'.format(jobid))
        cmd = 'mjobctl -c {0}'.format(jobid)
        ret = self.ssh.send_command(cmd)
        return ret



