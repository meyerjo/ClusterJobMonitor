import getpass
import json
import os
import re
from argparse import ArgumentParser
from subprocess import PIPE, STDOUT, Popen
from time import sleep

import paramiko
import logging

import xml.etree.ElementTree as ET

import sys


def get_output(out):
    log = logging.getLogger(__name__)
    try:
        return out.read().decode("utf-8")
    except BaseException as e:
        log.error(str(e))
        return ''


def check_job_state_is_running(xml_string, input_jobid):
    content = xml_string.strip()
    xml = ET.fromstring(content)
    if len(xml) != 1:
        return False, 'Len doesnt match expected'
    try:
        jobid = xml[0].attrib['JobID']
        state = xml[0].attrib['State']
        if jobid != str(input_jobid):
            return False, 'Wrong jobid {0}'.format(jobid)
        return (state == 'Running'), state
    except BaseException as e:
        log.error(str(e))
        return False, str(e)


def write_interactive_job_script(ssh_connection, scriptname, commandname=None, vncversion=None):
    import re
    log = logging.getLogger(__name__)
    if commandname is None:
        commandname = 'run_vncserver'
    if not re.search('.*run_vncserver.*', commandname):
        log.info('Specified commandname, doesn\'t match min expectation going to stop')
        commandname = 'run_vncserver'
    if vncversion is None:
        vncversion = '1.1.0'
    if not re.search('^1.[1,3].0$', vncversion):
        vncversion = '1.1.0'


    shell_script = ('#!/bin/bash\n'
                    'module load vis/tigervnc/{1}\n'
                    '{0} > $(echo ~/vnc_param_${{MOAB_JOBID}}.out)\n'
                    'while :\n'
                    'do\n'
                    'echo "Run loop forever"\n'
                    'sleep 2\n'
                    'done\n').format(commandname, vncversion)
    # shell_script = re.sub('{', '{{', shell_script)
    # shell_script = re.sub('}', '}}', shell_script)

    cmd = 'echo \'{0}\' > {1}; cat {1}'.format(shell_script, scriptname)
    stdin, stdout, stderr = ssh_connection.exec_command(cmd)
    stdout = get_output(stdout)

    if stdout == '':
        log.error('Apparently there was an error writing the script to the server going to stop')
        exit(2)


def generate_job_request(ssh_connection, resources):
    log = logging.getLogger(__name__)
    cmd = 'msub -l {0} tmp_interactive_job.sh'.format(resources)
    stdin, stdout, stderr = ssh_connection.exec_command(cmd)
    stdout = str(get_output(stdout))
    log.debug(str(stdout))
    m = re.search('([0-9]+)', stdout)
    if not m:
        log.error('Output doesn''t include an ID')
        exit(-1)
    jobid = int(m.group(1))
    return jobid


def wait_for_job_start(ssh_connection, jobid, wait_seconds=10):
    log = logging.getLogger(__name__)
    job_active = False
    while not job_active:
        log.info('Check if job {0} started'.format(jobid))
        try:
            stdin, stdout, stderr = ssh_connection.exec_command('checkjob -v -v --xml {0}'.format(jobid))
            stdout = str(get_output(stdout))
            if stdout != '':
                stdout = stdout.strip()
                job_active, current_state = check_job_state_is_running(stdout, jobid)
                if not job_active:
                    log.info('Job {0} isn''t active yet. Current state/error: {1}'.format(jobid, current_state))
        except BaseException as e:
            log.error(str(e))
        sleep(wait_seconds)


def cleanup_old_session(ssh_connection, failed_parameter_output):
    import re
    log = logging.getLogger(__name__)
    m = re.search('vncserver.+', failed_parameter_output)
    if not m:
        log.error('Failed to cleanup failed ssh session. Shouldn\'t happen')
        log.error('Failed parameter output content:\n{0}'.format(failed_parameter_output))
        return
    cmd = m.group(0)
    stdin, stdout, stderr = ssh_connection.exec_command(cmd)
    stdout = get_output(stdout)
    m = re.search('kill.+process\smanually', stdout)
    if not m:
        log.info('VNCServer should be killed, try to run script again')
        log.info('Contact me, if this doesn\'t match expectation: {0}'.format(stdout))
        return

    m = re.search(':[0-9]+', cmd)
    if not m:
        log.error('Didn\'t succeed in killing command with cmd "{0}"'.format(cmd))
    cmd = 'rm ~/.vnc/*{0}*.pid; rm ~/.vnc/*{0}*.log'.format(m.group(0))
    log.warning('Running the following command: {0}'.format(cmd))
    stdin, stdout, stderr = ssh_connection.exec_command(cmd)
    log.info('You can try to run the script again. Everything should be cleaned up')


def handle_failed_grep(ssh_connection, jobid, cleanup=False):
    """ Handles the failed grep. Outputs  the content of the vnc_param_%d.out(jobid) file and cancels the failed job request

    :param ssh_connection: paramiko ssh connection
    :param jobid: int jobid
    :return None
    """
    log = logging.getLogger(__name__)
    log.error('Grep of vnc_param failed')
    stdin, stdout, stderr = ssh_connection.exec_command('cat ~/vnc_param_{0}.out'.format(jobid))
    stdout = get_output(stdout)
    import re
    m = re.search('vncserver.+', stdout)
    if m:
        cmd = m.group(0)
        log.warning('Use following command to delete the current ssh session: \'{0}\''.format(m.group(0)))
        log.error('Usually this is the case, when you already have a job with an ssh connection. If you cannot kill it '
                  'with the given command, you can delete the files *.pid, *.log in ~/.vnc/')
        if cleanup:
            cleanup_old_session(ssh_connection, stdout)
    else:
        log.error('Content of ~/vnc_param_{0}.out\n{1}'.format(jobid, stdout))
        log.error('Usually this is the case, when you already have a job with an ssh connection. If you cannot kill it '
                  'with the given command, you can delete the files *.pid, *.log in ~/.vnc/')
    log.warning('Canceling the job request {0}'.format(jobid))
    stdin, stdout, stderr = ssh_connection.exec_command('canceljob {0}'.format(jobid))


def get_connection_settings(stdout):
    """ Return ssh, vnc connection settings

    :param stdout: stdout lines from vnc_param_%d.out file
    :return: ssh_vnc, vncviewer parameter
    """
    lines = stdout.split('\n')
    ssh_vnc = ''
    vncviewer = ''
    import re
    m =  re.search('ssh -fCNL.*', stdout)
    if m:
        ssh_vnc = m.group(0)
    m = re.search('vncviewer localhost:[0-9]+', stdout)
    if m:
        vncviewer = m.group(0)

    return ssh_vnc, vncviewer


def get_config_file(configfile):
    """ Opens the given configuration file, parses it and returns the object
    :param configfile: filename as string
    :returns json decoded object
    """
    with open(configfile, 'r') as config:
        content = config.read()
        obj = json.loads(content)
    return obj


def check_if_job_already_running(ssh_connection, jobname):
    """ Checks if jobs which match a specific name are already in queue
    :param ssh_connection: ssh paramiko ssh connection parameters
    :param jobname: str of the job we are looking for

    :returns array of jobs which match the specified JoName
    """
    stdin, stdout, stderr = ssh_connection.exec_command('showq  --xml')
    stdout = get_output(stdout)
    xml = ET.fromstring(stdout.strip())
    jobs = []
    for elem in xml:
        if elem.tag != 'queue':
            continue
        for job in elem:
            if 'JobName' not in job.attrib:
                continue
            if job.attrib['JobName'] == jobname:
                jobs.append(job.attrib)
    return jobs

def establish_ssh_connection(ssh_vnc, config):
    log = logging.getLogger(__name__)
    log.info('Trying to establish SSH Tunnel')
    command = ssh_vnc
    if sys.platform == 'win32' or sys.platform == 'cygwin':
        # cmd_wrapper = '"C:\\Program Files\\Git\\bin\\sh.exe" -c \'{0}\''
        cmd = ["C:\\Program Files\\Git\\bin\\sh.exe", '-c', '{0}'.format(command)]
    else:
        cmd = command.split(' ')

    if 'password' not in config:
        log.error('Config not in Password')
        return

    pw_byteencoded = config['password'].encode('utf-8')
    try:
        p = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        stdout_cmd = p.communicate(input=pw_byteencoded)[0]
    except BaseException as e:
        log.error('Error using Popen communication to SSH. Just send it as os.system command: {0}'.format(str(e)))
        os.system(' '.join(cmd))
    log.info('SSH Tunnel should be established: Open your VNC tool and connect to: "{0}"'.format(
        vncviewer[9:].strip()))

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-5.5s [%(name)s]'
               '[%(threadName)s][%(filename)s:%(funcName)s:%(lineno)d] %(message)s',
        level=logging.INFO)
    log = logging.getLogger(__name__)

    parser = ArgumentParser(description='Wrapper to get an interactive node')
    parser.add_argument('-r', '--resources', help='Resource Requirements of the job (default/example: nodes=1:ppn=4,pmem=4gb,walltime=0:08:00:00)',
                        default='nodes=1:ppn=4,pmem=4gb,walltime=0:08:00:00', nargs='?', type=str)
    parser.add_argument('-es', '--establish_sshtunnel', action='store_true', default=False)
    parser.add_argument('-cj', '--checkforjobtime', type=int,
                        help='Waiting time between two checkpoints whether a job started or not', default=10)
    parser.add_argument('-f', '--force', default=False, help='Force to generate job request', action='store_true')
    parser.add_argument('-ko', '--killoldjobs', default=False, help='Kills all old interactive jobs', action='store_true')
    parser.add_argument('-hn', '--hostname', type=str, help='Hostname of SSH server')
    parser.add_argument('-u', '--username', type=str, help='Username on SSH server')
    parser.add_argument('-c', '--configfile', help='Configfile with SSH Parameters for cluster (JSON-Formatted)', type=str)

    args = parser.parse_args()
    scriptname_cluster = 'tmp_interactive_job.sh'

    if args.configfile is None and (args.username is None or args.hostname is None):
        log.error('Neither a config file nor hostname, username is specified')
        parser.print_help()
        exit(-1)

    if args.configfile is not None:
        config = get_config_file(args.configfile)
        if 'hostname' not in config or 'username' not in config:
            log.error('Neither hostname nor username is specified in the configfile "{0}". Going to stop.'.format(args.configfile))
            exit(-1)
    else:
        config = dict(hostname=args.hostname,username=args.username)

    # ask the user to enter the password
    if 'password' not in config:
        log.info('Password is not provided. Please enter the password for user: "{0}" on server: "{1}"'.format(
            config['username'],
            config['hostname']
        ))
        password = getpass.getpass('Password: ')
        config['password'] = password

    log.info('Trying to establish connection to: {0} with username {1}'.format(config['hostname'], config['username']))
    # setting up ssh connection
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(config['hostname'], username=config['username'], password=config['password'], allow_agent=False, look_for_keys=False, timeout=60)
    except BaseException as e:
        log.error('Error during connection establishment: {0}'.format(str(e)))
        exit(-1)

    # check if a job is already setup
    jobs = check_if_job_already_running(ssh, scriptname_cluster)
    if len(jobs) > 0:
        log.warning('Already {0} jobs with the same jobname are active / or in queue'.format(len(jobs)))
        for job in jobs:
            log.info('Get Connection parameter for jobid {0}'.format(job['JobID']))
            stdin, stdout, stderr = ssh.exec_command("grep 'ssh\|vncviewer' ~/vnc_param_{0}.out".format(job['JobID']))
            stdout = get_output(stdout)
            if stdout != '':
                ssh_vnc, vncviewer = get_connection_settings(stdout)
                log.info('The following settings could be retrieved from an old vnc viewer file: ~/vnc_param_{0}.out'.format(job['JobID']))
                log.info('SSH: {0}'.format(ssh_vnc))
                log.info('VNCviewer: {0}'.format(vncviewer))
        # kill all old jobs
        if args.killoldjobs:
            jobids = [job['JobID'] for job in jobs]
            cmd = 'canceljob ' + ' '.join(jobids)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            log.info('Send following command "{0}"'.format(cmd))
            log.info('Output: {0}'.format(stdout.readlines()))
        if not args.force and not args.killoldjobs:
            ssh.close()
            exit(-1)

    # Send the shell script to the cluster
    log.info('Writing the interactive job script to the server ...')
    if 'custom_vnccommand' not in config:
        config['custom_vnccommand'] = 'run_vncserver'
    if 'custom_vncversion' not in config:
        config['custom_vncversion'] = '1.1.0'
    write_interactive_job_script(ssh, scriptname_cluster, config['custom_vnccommand'], config['custom_vncversion'])

    # Queue the interactive job
    log.info('Submitting the interactive job ...')
    jobid = generate_job_request(ssh, args.resources)

    # wait for jobid
    log.info('Submitted the interactive job. JobID: {0}'.format(jobid))
    wait_for_job_start(ssh, jobid, args.checkforjobtime)

    # our job is active now
    log.info('Interactive job is active')
    read_file_max = 3
    stdout = None
    for i in range(0, read_file_max):
        stdin, stdout, stderr = ssh.exec_command("cat ~/vnc_param_{0}.out".format(jobid))
        stdout = get_output(stdout)
        if (stdout is not None) and (stdout != ''):
            break
        else:
            log.info('VNC Parameter file seems to be empty, waiting for 3 seconds then try to read again')
            sleep(3)

    ssh_vnc, vncviewer = get_connection_settings(stdout)
    if ssh_vnc == '' or vncviewer == '':
        handle_failed_grep(ssh, jobid, cleanup=True)
    else:
        log.info('Establish SSH-Connection with the following command: "{0}"'.format(ssh_vnc))
        log.info('VNC Connection to "{0}"'.format(vncviewer[9:].strip()))
        # Write it to the console
        if args.establish_sshtunnel:
            establish_ssh_connection(ssh_vnc, config)

    ssh.close()
