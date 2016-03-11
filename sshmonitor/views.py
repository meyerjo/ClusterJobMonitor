import logging

from pyramid.view import view_config

from sshmonitor import SSHBasedJobManager


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'SSHMonitor'}


class JobRequests():

    def __init__(self, request):
        self._request = request

    @view_config(route_name='jobs', renderer='templates/jobs.pt')
    def all_jobs(self):
        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)

        coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode']
        jobs = ssh_jobmanager.get_all_jobs(coltitles)

        return {'project': 'SSHMonitor', 'jobs': jobs}


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
        jobs = ssh_jobmanager.get_all_jobs(coltitles)
        return {'project': 'SSHMonitor', 'jobs': jobs}


    @view_config(route_name='job_details', renderer='templates/jobs.pt')
    def job_details(self):
        log = logging.getLogger(__name__)

        details_jobid = self._request.matchdict['jobid']
        log.info('Request details for jobid {0}'.format(details_jobid))

        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHBasedJobManager(ssh_holder)
        coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode']
        jobs = ssh_jobmanager.get_all_jobs(coltitles)
        return_details = ssh_jobmanager.get_job_details(details_jobid)

        return {'project': 'SSHMonitor', 'jobs': jobs, 'details': return_details}
