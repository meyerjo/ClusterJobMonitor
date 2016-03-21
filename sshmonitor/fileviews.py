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


class FileViews:


    def __init__(self, request):
        self._request = request


    @view_config(route_name='filemonitor', renderer='templates/filemonitoring.pt')
    def dummy(request):
        return {'error': 'not yet implemented', 'project': 'Not yet implemented'}

    def _get_monitored_files(self, path):
        res = DBSession.query(MonitoredFile.complete_filepath,
                              MonitoredFile.filename,
                              MonitoredFile.folder).filter(MonitoredFile.folder == path).all()
        complete_filename = [r[0] for r in res]
        filename = [r[1] for r in res]
        folder = [r[2] for r in res]
        return complete_filename, filename, folder

    @view_config(route_name='filemonitor_editor', renderer='templates/filemonitoring.pt')
    def filemonitoring(self):
        log = logging.getLogger(__name__)
        if self._request.matchdict['modus'] == 'add':
            if self._request.matchdict['options'] == 'files':
                if self._request.params is not []:
                    # TODO: add this information to the file
                    md5_enabled = True if 'withmd5' in self._request.params and self._request.params['withmd5'] == '0' else False
                    all_files = self._request.params.getall('file')

                    complete_file, filenames, folders = self._get_monitored_files(self._request.params['folder'] + '/')

                    log.info(complete_file)

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