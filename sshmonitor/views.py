from pyramid.view import view_config

from sshmonitor import JobManager
from sshmonitor.filebasedjobmanager import FileBasedJobManager


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'SSHMonitor'}


@view_config(route_name='jobs', renderer='templates/jobs.pt')
def all_jobs(request):

    jobmanager = request.registry.settings['jobmanager']
    coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode']

    jobs = jobmanager.get_all_jobs(coltitles)


    return {'project': 'SSHMonitor', 'jobs': jobs}