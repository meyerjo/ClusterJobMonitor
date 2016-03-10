from pyramid.view import view_config

from sshmonitor import SSHBasedJobManager


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'SSHMonitor'}


@view_config(route_name='jobs', renderer='templates/jobs.pt')
def all_jobs(request):
    ssh_holder = request.registry.settings['ssh_holder']
    ssh_jobmanager = SSHBasedJobManager(ssh_holder)
    coltitles = ['JobID', 'JobName', 'StartTime', 'SubmissionTime', 'CompletionTime', 'State', 'CompletionCode']
    jobs = ssh_jobmanager.get_all_jobs(coltitles)

    return {'project': 'SSHMonitor', 'jobs': jobs}