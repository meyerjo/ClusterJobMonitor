import logging

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


    def _from_basic_showq(self, classname, filteroptions=None):
        log = logging.getLogger(__name__)
        log.debug('Querying {0} jobs'.format(classname))
        return_dict =  self.ssh.send_command('showq --xml')
        if return_dict['error'] is None:
            lines = return_dict['stdoutstr']
            tree = ET.fromstring(lines)

            return self._load_class_from_xml(tree, classname, filteroptions)
        else:
            return return_dict

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
        return_dict =  self.ssh.send_command('showq --xml -c')
        if return_dict['error'] is None:
            lines = return_dict['stdoutstr']
            tree = ET.fromstring(lines)

            return self._load_class_from_xml(tree, 'completed', filteroptions)
        else:
            return return_dict

    def get_job_details(self, jobid):
        cmd = 'checkjob --xml {0}'.format(jobid)
        log = logging.getLogger(__name__)
        log.debug('Checking job details for {0}'.format(jobid))

        output = self.ssh.command(jobid)



        pass

    def submit_job(self, job):
        pass

    def cancel_job(self, jobid):
        log = logging.getLogger(__name__)
        log.info('Cancel job with id: {0}'.format(jobid))
        cmd = 'mjobctl -c {0}'.format(jobid)
        ret = self.ssh.send_command(cmd)
        return ret



