import logging

import paramiko
import sys


class SSHConnectionHolder:

    def __init__(self, ssh_param):
        self.ssh_param = ssh_param
        self.ssh = None
        self._establish_connection(ssh_param)


    def _establish_connection(self, ssh_param):
        log = logging.getLogger(__name__)
        if 'server' in ssh_param:
            if 'authentication' in ssh_param:
                if ssh_param['authentication'] == 'username_password':
                    if 'username' in ssh_param and 'password' in ssh_param:
                        log.info('Establish Server, Username, Password connection via SSH')
                        try:
                            self.ssh = paramiko.SSHClient()
                            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                            self.ssh.connect(ssh_param['server'],
                                             username=ssh_param['username'],
                                             password=ssh_param['password'])
                        except BaseException as e:
                            log.error('Error during ssh connection {0}'.format(str(e)))
                    else:
                        log.error('Fields username/password do not exist')
                else:
                    log.error('Not yet implemented')
            else:
                log.error('Authentication field missing')
        else:
            log.error('No server specified')

    def send_command(self, command):
        if self.ssh is None:
            return dict(error='No ssh connection')
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            lines = stdout.readlines()
            lines = ''.join(lines)

            return dict(error=None, stdin=stdin, stdout=stdout,
                        stderr=stderr, stdoutstr=lines)
        except BaseException as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            log = logging.getLogger(__name__)
            log.error(str(e))
            return dict(error=str(e), errordetails=exc_tb.tb_lineno)