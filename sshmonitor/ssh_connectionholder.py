import logging

import paramiko


class SSHConnectionHolder:

    def __init__(self, ssh_param):
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

    def send_command(self, command):
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)

            lines = stdout.readlines()
            lines = ''.join(lines)

            return dict(error=None, stdin=stdin.readlines(), stdout=stdout.readlines(),
                        stderr=stderr.readlines(), stdoutstr=lines)
        except BaseException as e:
            return dict(error=str(e))