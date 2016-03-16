import paramiko
from paramiko import SSHClient


class SSHTest:

    @staticmethod
    def test(param):
        if not ('server' in param and 'port' in param and 'username' in param and 'password' in param):
            return dict(error='Field missing: {0} '.format(param.keys()))

        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(param['server'], port=param['port'], username=param['username'], password=param['password'])
            stdin, stdout, stderr = ssh.exec_command('echo Test')
            stdout_lines = stdout.readlines()
        except BaseException as e:
            return dict(error=str(e))
        finally:
            ssh.close()
        print(stdout_lines)
        if stdout_lines == ['Test\n']:
            return dict(error=None)
        return dict(error='Output doesn\'t match the expected one')
