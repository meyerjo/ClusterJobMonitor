import logging
import re

import jsonpickle
import sys
from pyramid.request import Request
from pyramid.view import view_config

from jobmanager.job_database_wrapper import JobDatabaseWrapper
from models import DBSession
from models.Job import Job, JobOutput
from jobmanager.sshbasedjobmanager import SSHBasedJobManager
from ssh.run_clusterjob import JobSubmitStatement


class JobRequests():

    def __init__(self, request):
        self._request = request
        if 'title' in self._request.registry.settings:
            self._projectname = self._request.registry.settings['title']
        else:
            self._projectname = 'ClusterManagement'
        self._coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime',
                           'CompletionTime', 'State', 'CompletionCode', 'AWDuration', 'ReqAWDuration', 'ReqProcs']

    def _get_current_jobs(self, jobmanager, coltitles):
        jobs = JobDatabaseWrapper.get_jobs(jobmanager, coltitles)
        new_job_obj = dict(joborder=jobs['joborder'], jobs=dict())
        for order in jobs['joborder']:
            if order not in jobs:
                continue
            current_header = jobs[order]['header']
            new_job_obj['jobs'][order] = dict()
            for job in jobs[order]['body']:
                if job[current_header.index('JobName')] not in new_job_obj['jobs'][order]:
                    new_job_obj['jobs'][order][job[current_header.index('JobName')]] = [dict(zip(current_header, job))]
                else:
                    new_job_obj['jobs'][order][job[current_header.index('JobName')]].append(dict(zip(current_header, job)))
        return new_job_obj

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

    @view_config(route_name='cancel_job_basic', renderer='templates/jobs.pt', request_method='POST')
    @view_config(route_name='cancel_job', renderer='json', request_method='POST', match_param='jobid=json')
    def cancel_job_post(self):
        log = logging.getLogger(__name__)
        opts = self._request.params
        elements = []
        opts = dict(opts)
        for key, val in opts.items():
            if re.search('^[0-9]+$', val):
                elements.append(val)
                #ssh_holder = self._request.registry.settings['ssh_holder']
                #ssh_jobmanager = SSHBasedJobManager(ssh_holder)
                #return_canceljob = ssh_jobmanager.cancel_job(val)
                #elements.append(return_canceljob)
        log.info(elements)
        if self._request.matched_route.name == 'cancel_job':
            return dict(error=None, jobs=elements)
        subreq = Request.blank(self._request.route_url('jobs'))
        return self._request.invoke_subrequest(subreq)


    @view_config(route_name='cancel_job',  renderer='templates/jobs.pt')
    def cancel_job(self):
        log = logging.getLogger(__name__)
        cancel_jobid = self._request.matchdict['jobid']
        log.info('Cancel Request for job: {0}'.format(cancel_jobid))
        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)
        return_canceljob = ssh_jobmanager.cancel_job(cancel_jobid)
        log.info(return_canceljob)

        subreq = Request.blank(self._request.route_url('jobs'))
        return self._request.invoke_subrequest(subreq)


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

    def get_most_keys(self):
        jobarchive = JobDatabaseWrapper().job_archive()
        max_keys = []
        examples = []
        for job in jobarchive:
            if len(job.keys()) > len(max_keys):
                max_keys = job.keys()
                examples = job
        return max_keys, examples

    @view_config(route_name='jobarchive', renderer='templates/jobarchive.pt')
    def job_archive(self):
        jobarchive_config = JobDatabaseWrapper().job_archive_config()
        all_available_keys, examples = self.get_most_keys()
        if jobarchive_config is None:
            keys = all_available_keys
        else:
            jobarchive_config = jsonpickle.decode(jobarchive_config[1])
            keys = jobarchive_config
        return {'project': self._projectname, 'jobarchive': JobDatabaseWrapper().job_archive(), 'visible_keys': keys}

    @view_config(route_name='jobarchive_config', renderer='templates/jobarchive_config.pt')
    def job_archive_config(self):
        # get the row with the most keys
        jobarchive_config = JobDatabaseWrapper().job_archive_config()
        all_available_keys, examples = self.get_most_keys()
        if jobarchive_config is None:
            keys = [(key, True) for key in all_available_keys]
        else:
            jobarchive_config = jsonpickle.decode(jobarchive_config[1])
            not_activated_keys = []
            for key in all_available_keys:
                if key not in jobarchive_config:
                    not_activated_keys.append((key, False))
            keys = [(key, True) for key in jobarchive_config]
            keys = keys + not_activated_keys

        return {'project': self._projectname, 'keys': keys, 'examples': examples}

    @view_config(route_name='jobarchive_config', renderer='json', request_method='POST')
    def job_archive_config(self):
        post_list = self._request.POST
        post_dict = post_list.__dict__
        post_list = post_dict['_items']
        keys = []
        for key in post_list:
            if key[0] == 'checkbox':
                keys.append(key[1])

        JobDatabaseWrapper().write_job_archive_config(keys)
        subreq = Request.blank(self._request.route_path('jobarchive_config'))
        return self._request.invoke_subrequest(subreq)



