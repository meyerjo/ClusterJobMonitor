import logging
import os

import re
import transaction
from pyramid.request import Request
from pyramid.view import view_config
from webob.multidict import NestedMultiDict

from models import DBSession
from models.FileMonitorModels import MonitoredFile
from ssh.sshfilebrowser import SSHFileBrowser
from sshmonitor import SSHBasedJobManager
from sshmonitor.filemonitor import FileMonitor


class FileViews:


    def __init__(self, request):
        self._request = request


    @view_config(route_name='filemonitor', renderer='json')
    def dummy(self):
        log = logging.getLogger(__name__)
        files = FileMonitor(SSHFileBrowser(self._request.registry.settings['ssh_holder']))
        for file in files.get_monitored_files():
            print(file.id, file.filename)
            print(file.__dict__)
            print(dir(file))
        log.error('not yet implemented')
        return {'error': 'not yet implemented', 'project': 'Not yet implemented', 'content': ''}

    def _get_monitored_files(self, path):
        files = FileMonitor(SSHFileBrowser(self._request.registry.settings['ssh_holder']))
        res = files.get_monitored_files()
        complete_filename = [r.complete_filepath for r in res]
        filename = [r.filename for r in res]
        folder = [r.folder for r in res]
        return complete_filename, filename, folder

    @view_config(route_name='filemonitor_editor', renderer='templates/filemonitoring.pt', match_param=('modus=add', 'options=files'))
    def filemonitoring(self):
        log = logging.getLogger(__name__)
        if self._request.params:
            # TODO: add this information to the file
            md5_enabled = True if 'withmd5' in self._request.params and self._request.params['withmd5'] == '0' else False
            all_files = self._request.params.getall('file')

            complete_file, filenames, folders = self._get_monitored_files(self._request.params['folder'] + '/')

            with transaction.manager:
                for f in all_files:
                    if f in complete_file:
                        log.debug('Skipping file {0}, because it is already monitored'.format(f))
                        continue
                    (path, filename) = os.path.split(f)
                    dbobj = MonitoredFile(path, filename, f)
                    DBSession.add(dbobj)
                DBSession.commit()
            files_not_mentioned = [c for c in complete_file if c not in all_files]
            # TODO: decide on this
            log.info('TODO: Still have to decide whether files which are not selected should be deleted or not.'
                     'Affected files would be: {0}'.format(files_not_mentioned))
        else:
            log.info('Got an empty request, going to redirect to start page')
            subreq = Request.blank('/')
            return self._request.invoke_subrequest(subreq)

        subreq = Request.blank(self._request.route_path('filebrowser'),
                               POST=dict(folder=self._request.params['folder'],
                                         currentfolder=self._request.params['currentfolder'],
                                         pathdescription='abs'))
        return self._request.invoke_subrequest(subreq)


    @view_config(route_name='filebrowser', renderer='templates/filemonitoring.pt')
    def browse_files(self):
        log = logging.getLogger(__name__)
        if 'ssh_holder' not in self._request.registry.settings:
            return dict(project='FileBrowser', content=[])
        ssh_holder = self._request.registry.settings['ssh_holder']
        ssh_jobmanager = SSHFileBrowser(ssh_holder)
        folder = self._request.params['folder'] if 'folder' in self._request.params else '.'
        currentfolder = self._request.params['currentfolder'] if 'currentfolder' in self._request.params else '.'
        reference_type = self._request.params['pathdescription'] if 'pathdescription' in self._request.params else 'rel'
        # do some reference mambo jambo
        if reference_type == 'rel':
            if folder == '.':
                folder_request = '.'
            else:
                folder_request = '{0}/{1}'.format(currentfolder, folder)
        elif reference_type == 'abs':
            if folder == '':
                folder_request = currentfolder
            else:
                folder_request = folder
        else:
            log.info('Unknown request type {0}'.format(reference_type))
            folder_request = '.'

        log.info('Requesting folder: {0}'.format(folder_request))
        output = ssh_jobmanager.get_folder_content(folder_request)
        return {'project': 'FileBrowser', 'content': output}