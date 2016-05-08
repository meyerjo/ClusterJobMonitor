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


logging.basicConfig(
    format='%(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s][%(filename)s:%(funcName)s:%(lineno)d] %(message)s',
    level=logging.INFO)
log = logging.getLogger(__name__)


def get_output(out):
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


def write_interactive_job_script(ssh_connection, scriptname):
    shell_script = ('#!/bin/bash\n'
                    'module load vis/tigervnc/1.1.0\n'
                    'run_vncserver > ~/vnc_param.out\n'
                    'while :\n'
                    'do\n'
                    'echo "Run loop forever"\n'
                    'sleep 2\n'
                    'done\n')

    cmd = 'echo \'{0}\' > {1}; cat {1}'.format(shell_script, scriptname)
    stdin, stdout, stderr = ssh_connection.exec_command(cmd.format(shell_script))
    stdout = get_output(stdout)

    if stdout == '':
        log.error('Apparently there was an error writing the script to the server going to stop')
        exit(2)
    if stdout.strip() != shell_script.strip():
        log.error('Writing doesn''t yield the expected result')
        log.error('Written content:\n{0}'.format(stdout.strip()))
        exit(2)


def generate_job_request(ssh_connection, resources):
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
    job_active = False
    while not job_active:
        log.debug('Check if job started')
        try:
            stdin, stdout, stderr = ssh_connection.exec_command('checkjob --xml {0}'.format(jobid))
            stdout = str(get_output(stdout))
            if stdout != '':
                stdout = stdout.strip()
                job_active, current_state = check_job_state_is_running(stdout, jobid)
                if not job_active:
                    log.info('Job {0} isn''t active yet. Current state: {1}'.format(jobid, current_state))
        except BaseException as e:
            log.debug(str(e))
        sleep(wait_seconds)


def handle_failed_grep(ssh_connection, jobid):
    log.error('Grep of vnc_param failed')
    stdin, stdout, stderr = ssh_connection.exec_command('cat ~/vnc_param.out')
    stdout = get_output(stdout)
    log.error('Content of ~/vnc_param.out\n{0}'.format(stdout))
    log.error('Usually this is the case, when you already have a job with an ssh connection. If you cannot kill it '
              'with the given command, you can delete the files *.pid, *.log in ~/.vnc/')
    log.warning('Canceling the job request {0}'.format(jobid))
    stdin, stdout, stderr = ssh_connection.exec_command('canceljob {0}'.format(jobid))


def get_connection_settings(stdout):
    lines = stdout.split('\n')
    ssh_vnc = ''
    vncviewer = ''
    for line in lines:
        if line.startswith('ssh'):
            ssh_vnc = line
        elif line.startswith('vncviewer'):
            vncviewer = line
    return ssh_vnc, vncviewer


def get_config_file(configfile):
    """ Opens the given configuration file, parses it and returns the object"""
    with open(configfile, 'r') as config:
        content = config.read()
        obj = json.loads(content)
    return obj


def check_if_job_already_running(ssh_connection, jobname):
    stdin, stdout, stderr = ssh_connection.exec_command('showq --xml')
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


if __name__ == '__main__':
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

    if 'password' not in config:
        log.info('Password is not provided. Please enter the password for user: "{0}" on server: "{1}"'.format(
            config['username'],
            config['hostname']
        ))
        password = getpass.getpass('Password: ')
        config['password'] = password

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(config['hostname'], username=config['username'], password=config['password'])

    jobs = check_if_job_already_running(ssh, 'tmp_interactive_job.sh')
    if len(jobs) > 0:
        log.warning('Already {0} jobs with the same jobname are active / or in queue'.format(len(jobs)))
        stdin, stdout, stderr = ssh.exec_command("grep 'ssh\|vncviewer' ~/vnc_param.out")
        stdout = get_output(stdout)
        if stdout != '':
            ssh_vnc, vncviewer = get_connection_settings(stdout)
            log.info('The following settings could be retrieved from an old vnc viewer file.')
            log.info('SSH: {0}'.format(ssh_vnc))
            log.info('VNCviewer: {0}'.format(vncviewer))
        if args.killoldjobs:
            jobids = [job['JobID'] for job in jobs]
            cmd = 'canceljob ' + ' '.join(jobids)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            log.info('Send following command "{0}"'.format(cmd))
            log.info('Output: {0}'.format(stdout.readlines()))
        if not args.force:
            exit(-1)

    # Send the shell script to the cluster
    log.info('Writing the interactive job script to the server ...')
    write_interactive_job_script(ssh, 'tmp_interactive_job.sh')

    # Queue the interactive job
    log.info('Submitting the interactive job ...')
    jobid = generate_job_request(ssh, args.resources)

    # wait for jobid
    log.info('Submitted the interactive job. JobID: {0}'.format(jobid))
    wait_for_job_start(ssh, jobid, args.checkforjobtime)

    # our job is active now
    log.info('Interactive job is active')
    stdin, stdout, stderr = ssh.exec_command("grep 'ssh\|vncviewer' ~/vnc_param.out")
    stdout = get_output(stdout)
    if stdout == '':
        handle_failed_grep(ssh, jobid)
    else:
        ssh_vnc, vncviewer = get_connection_settings(stdout)
        log.info('Establish SSH-Connection with the following command: "{0}"'.format(ssh_vnc))
        log.info('VNC Connection to "{0}"'.format(vncviewer[9:].strip()))
        # Write it to the console
        if args.establish_sshtunnel:
            log.info('Trying to establish SSH Tunnel')
            command = ssh_vnc
            if sys.platform == 'win32' or sys.platform == 'cygwin':
                # cmd_wrapper = '"C:\\Program Files\\Git\\bin\\sh.exe" -c \'{0}\''
                cmd = ["C:\\Program Files\\Git\\bin\\sh.exe",  '-c', '{0}'.format(command)]
            else:
                cmd = command.split(' ')

            pw_byteencoded = config['password'].encode('utf-8')
            try:
                p = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
                stdout_cmd = p.communicate(input=pw_byteencoded)[0]
                print(stdout_cmd.decode())
            except BaseException as e:
                log.error('Error using Popen communication to SSH. Just send it as cmd request')
                # os.system(' '.join(cmd))
            log.info('SSH Tunnel should be established: Open your VNC tool and connect to: "{0}"'.format(
                vncviewer[9:].strip()))
    ssh.close()
