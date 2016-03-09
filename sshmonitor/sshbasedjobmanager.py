import logging

import paramiko

from sshmonitor import JobManager
import xml.etree.ElementTree as ET


class SSHBasedJobManager(JobManager):

    def __init__(self, ssh_param):
        # establish ssh connection
        assert(isinstance(ssh_param, dict))
        log = logging.getLogger(__name__)
        self.ssh_param = ssh_param
        self._establish_connection(ssh_param)

    def _establish_connection(self, ssh_param):
        log = logging.getLogger(__name__)
        if 'server' in ssh_param:
            if 'authentication' in ssh_param:
                if ssh_param['authentication'] == 'username_password':
                    if 'username' in ssh_param and 'password' in ssh_param:
                        self.ssh = paramiko.SSHClient()
                        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        self.ssh.connect(ssh_param['server'],
                                         username=ssh_param['username'],
                                         password=ssh_param['password'])
                    else:
                        log.error('Fields username/password do not exist')
                else:
                    log.error('Not yet implemented')
            else:
                log.error('Authentication field missing')
        else:
            log.error('No server specified')

    def _send_command(self, command):
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)

            lines = stdout.readlines()
            lines = ''.join(lines)

            return dict(error=None, stdin=stdin, stdout=stdout, stderr=stderr, stdoutstr=lines)
        except BaseException as e:
            return dict(error=str(e))

    def _from_basic_showq(self, classname, filteroptions=None):
        log = logging.getLogger(__name__)
        log.debug('Querying {0} jobs'.format(classname))
        return_dict =  self._send_command('showq --xml')
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
        return_dict =  self._send_command('showq --xml -c')
        if return_dict['error'] is None:
            lines = return_dict['stdoutstr']
            tree = ET.fromstring(lines)

            return self._load_class_from_xml(tree, 'completed', filteroptions)
        else:
            return return_dict

    def get_job_details(self, jobid):
        pass

    def submit_job(self, job):
        pass

    def cancel_job(self, jobid):
        log = logging.getLogger(__name__)
        log.info('Cancel job with id: {0}'.format(jobid))
        cmd = 'mjobctl -c {0}'.format(jobid)
        ret = self._send_command(cmd)
        return ret



