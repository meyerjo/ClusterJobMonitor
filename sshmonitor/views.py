import logging

import re

import jsonpickle
import transaction
from pyramid.view import view_config

from models import DBSession
from models.Job import Job, JobOutput
from sshmonitor import SSHBasedJobManager
from sshmonitor.job_database_wrapper import JobDatabaseWrapper


class JobRequests():

    def __init__(self, request):
        self._request = request
        if 'title' in self._request.registry.settings:
            self._projectname = self._request.registry.settings['title']
        else:
            self._projectname = 'ClusterManagement'
        self._coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode']

    def _get_current_jobs(self, jobmanager, coltitles):
        return JobDatabaseWrapper.get_jobs(jobmanager, coltitles)

    @view_config(route_name='jobs', renderer='templates/jobs.pt')
    def all_jobs(self):
        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)
        jobs = self._get_current_jobs(ssh_jobmanager, self._coltitles)

        log = logging.getLogger(__name__)
        try:
            JobDatabaseWrapper().job_archive()
        except BaseException as e:
            log.error(str(e))

        return {'project': self._projectname,
                'jobs': jobs}

    @view_config(route_name='cancel_job', renderer='templates/jobs.pt')
    def cancel_job(self):
        log = logging.getLogger(__name__)
        cancel_jobid = self._request.matchdict['jobid']
        log.info('Cancel Request for job: {0}'.format(cancel_jobid))
        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)
        return_canceljob = ssh_jobmanager.cancel_job(cancel_jobid)
        log.info(return_canceljob)

        jobs = self._get_current_jobs(ssh_jobmanager, self._coltitles)
        return {'project': self._projectname, 'jobs': jobs}

    @view_config(route_name='job_details', renderer='templates/jobs.pt')
    def job_details(self):
        log = logging.getLogger(__name__)
        details_jobid = self._request.matchdict['jobid']
        log.info('Request details for jobid {0}'.format(details_jobid))
        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)
        jobs = self._get_current_jobs(ssh_jobmanager, self._coltitles)
        return_details = ssh_jobmanager.get_job_details(details_jobid)

        # write details to the database
        job = DBSession.query(Job).filter(Job.id == details_jobid).first()
        if job is not None:
            job.jobdetails = jsonpickle.encode(return_details)
            DBSession.commit()
        return {'project': self._projectname,
                'jobs': jobs,
                'details': return_details}

    @view_config(route_name='joboutput', renderer='templates/jobs.pt')
    def job_output(self):
        log = logging.getLogger(__name__)

        jobid = self._request.matchdict['jobid']
        log.info('Request job output for id:{0}'.format(jobid))

        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)

        jobs = self._get_current_jobs(ssh_jobmanager, self._coltitles)
        joboutput = ssh_jobmanager.get_job_output(jobid)

        if 'error' in joboutput and joboutput['error'] is None:
            db_joboutput = JobOutput(id=jobid, output=jsonpickle.encode(joboutput))
            DBSession.add(db_joboutput)
            DBSession.commit()

        if 'error' in joboutput and joboutput['error'] is not None:
            jobresult = joboutput['error']
        else:
            jobresult = joboutput['content']
            jobresult = ''.join(jobresult)
        if 'type' not in joboutput:
            joboutput['type'] = 'type field missing'

        return {'project': self._projectname,
                'jobs': jobs,
                'output': dict(jobid=jobid, output=jobresult, type=joboutput['type'])}
