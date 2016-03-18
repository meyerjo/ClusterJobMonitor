import logging

from pyramid.view import view_config

from ssh.sshfilebrowser import SSHFileBrowser
from sshmonitor import SSHBasedJobManager


class FileViews:


    def __init__(self, request):
        self._request = request


    @view_config(route_name='filemonitor', renderer='templates/filemonitoring.pt')
    @view_config(route_name='filemonitor_editor', renderer='templates/filemonitoring.pt')
    def dummy(request):
        return {'error':'not yet implemented', 'project': 'Not yet implemented'}

    @view_config(route_name='filebrowser', renderer='templates/filemonitoring.pt')
    def browse_files(self):
        log = logging.getLogger(__name__)
        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHFileBrowser(ssh_holder)
        print(self._request.params)
        folder = self._request.params['folder'] if 'folder' in self._request.params else '.'
        currentfolder = self._request.params['currentfolder'] if 'currentfolder' in self._request.params else '.'
        if folder.startswith('/'):
            folder_request = folder
        elif folder == '.':
            folder_request = '.'
        else:
            folder_request = '{0}/{1}'.format(currentfolder, folder)
        log.info('Requesting folder: {0}'.format(folder_request))
        output = ssh_jobmanager.get_folder_content(folder_request)
        print(output)

        return {'project': 'FileBrowser', 'content': output}