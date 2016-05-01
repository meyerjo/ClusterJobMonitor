import logging
import socket

import paramiko
import sys

from scp import SCPClient

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

    def _read_output(self, input):
        try:
            return dict(error=None, content=input.readlines())
        except BaseException as e:
            return dict(error=str(e), content=None)

    def connection_alive(self):
        log = logging.getLogger(__name__)
        if self.ssh is None:
            return False
        try:
            x = self.ssh.get_transport().is_active()
            return True
        except BaseException as e:
            log.error('Connection alive: {0}'.format(str(e)))
            return False

    def send_command(self, command):
        log = logging.getLogger(__name__)
        if self.ssh is None:
            return dict(error='No ssh connection')
        if not self.connection_alive():
            self._establish_connection(self.ssh_param)
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)

            stdin = self._read_output(stdin)
            stdout = self._read_output(stdout)
            stderr = self._read_output(stderr)

            if stdout['error'] is None:
                lines = ''.join(stdout['content'])
            else:
                lines = '<error>{0}</error>'.format(stdout['error'])

            return dict(error=None, stdin=stdin, stdout=stdout,
                        stderr=stderr, stdoutstr=lines, errordetails=None)
        except socket.error as e:
            log.error('Connection error with paramiko ssh client: {0}'.format(str(e)))
            return dict(error=str(e), errordetails=None)
        except BaseException as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            log.error(str(e))
            # reset connection once it is not alive anymore
            return dict(error=str(e), errordetails=exc_tb.tb_lineno)
