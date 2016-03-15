import logging

import re

import jsonpickle
from pyramid.view import view_config

from models import DBSession
from models.Job import Job
from sshmonitor import SSHBasedJobManager


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'SSHMonitor'}


class JobRequests():

    def __init__(self, request):
        self._request = request
        self._projectname = 'ClusterManagement'

    def _write_jobinfo_to_db(self, jobs):
        log = logging.getLogger(__name__)
        for (classname, classmembers) in jobs.items():
            if len(classmembers) > 0:
                for element in classmembers:
                    if 'JobID' in element and re.search('[0-9]*', element['JobID']):
                        dbrow = DBSession.query(Job).filter(Job.id == element['JobID']).all()
                        if len(dbrow) == 0:
                            j = Job(element['JobID'], jsonpickle.encode(element))
                            DBSession.add(j)
                        elif len(dbrow) == 1:
                            dbrow[0].jobinfo = jsonpickle.encode(element)
                        else:
                            log.info('More than one entry for jobid')
                    else:
                        log.debug('Row didnt match specified criteria {0}'.format(element))
        DBSession.commit()


    def _get_current_jobs(self, jobmanager, coltitles):
        jobs = jobmanager.get_all_jobs()
        log = logging.getLogger(__name__)
        try:
            self._write_jobinfo_to_db(jobs)
        except BaseException as e:
            log.error(str(e))

        jobs = jobmanager.filter_from_dict(jobs, coltitles)
        jobs = jobmanager.convert_from_listdict_to_list(jobs, coltitles)
        return jobs


    @view_config(route_name='jobs', renderer='templates/jobs.pt')
    def all_jobs(self):
        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)

        coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode']
        jobs = self._get_current_jobs(ssh_jobmanager, coltitles)

        return {'project': self._projectname, 'jobs': jobs}


    @view_config(route_name='cancel_job', renderer='templates/jobs.pt')
    def cancel_job(self):
        log = logging.getLogger(__name__)
        cancel_jobid = self._request.matchdict['jobid']
        log.info('Cancel Request for job: {0}'.format(cancel_jobid))
        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)
        return_canceljob = ssh_jobmanager.cancel_job(cancel_jobid)
        log.info(return_canceljob)

        coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode']
        jobs = self._get_current_jobs(ssh_jobmanager, coltitles)
        return {'project': self._projectname, 'jobs': jobs}


    @view_config(route_name='job_details', renderer='templates/jobs.pt')
    def job_details(self):
        log = logging.getLogger(__name__)

        details_jobid = self._request.matchdict['jobid']
        log.info('Request details for jobid {0}'.format(details_jobid))

        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)
        coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode']
        jobs = self._get_current_jobs(ssh_jobmanager, coltitles)
        return_details = ssh_jobmanager.get_job_details(details_jobid)


        # write details to the database
        job = DBSession.query(Job).filter(Job.id == details_jobid).first()
        if job is not None:
            job.jobdetails = jsonpickle.encode(return_details)
            DBSession.commit()
        return {'project': self._projectname, 'jobs': jobs, 'details': return_details}


    @view_config(route_name='joboutput', renderer='templates/jobs.pt')
    def job_output(self):
        log = logging.getLogger(__name__)

        jobid = self._request.matchdict['jobid']
        log.info('Request job output for id:{0}'.format(jobid))

        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)

        coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode']
        jobs = self._get_current_jobs(ssh_jobmanager, coltitles)

        joboutput = ssh_jobmanager.get_job_output(jobid)
        jobresult = None
        if 'error' in joboutput and joboutput['error'] is not None:
            jobresult = joboutput['error']
        else:
            jobresult = joboutput['content']
            jobresult = ''.join(jobresult)

        return {'project': self._projectname, 'jobs': jobs, 'output': dict(jobid=jobid, output=jobresult)}
