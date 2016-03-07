from pyramid.view import view_config

from sshmonitor import JobManager


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'SSHMonitor'}


@view_config(route_name='jobs', renderer='templates/jobs.pt')
def all_jobs(request):

    t = JobManager('jobs.xml')
    jobs = t.get_all_jobs(['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode'])

    return {'project': 'SSHMonitor', 'jobs': jobs}