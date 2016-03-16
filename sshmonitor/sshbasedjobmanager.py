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
            if lines == '':
                return dict(error='Non existing jobid')
            try:
                xml_output = ET.fromstring(lines)
            except BaseException as e:
                return dict(error=str(e))
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

    def get_job_output(self, jobid):
        log = logging.getLogger(__name__)
        log.info('Retrieve job info')

        details = self.get_job_details(jobid)
        if ('error' in details) and (details['error'] is not None):
            log.error(details['error'])
            return details
        try:
            stdout = details['StdOut']
            stdout = stdout.replace('%j', '%i')
            jobid = details['JobID']
            expected_file = stdout % int(jobid)
        except BaseException as e:
            log.error('Error during expected file retrieval {0}'.format(str(e)))
            details['error'] = 'Error during expected file retrieval {0}'.format(str(e))
            return details

        output = self.ssh.send_command('cat {0}'.format(expected_file))
        if 'error' in output and output['error'] is not None:
            log.warning('Error in response')
            return output

        if 'error' in output['stdout'] and output['stdout']['error'] is not None:
            log.warning('Error in stdout structure')
            return output['stdout']

        stdout = output['stdout']
        stdout['type'] = 'stdout'
        if not stdout['content']:
            if 'stderr' in output:
                if output['stderr']['content']:
                    stdout = output['stderr']
                    stdout['type'] = 'stderr'
        return stdout



