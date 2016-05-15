import logging

from models import DBSession
from models.FileMonitorModels import MonitoredFile


class FileMonitor:

    def __init__(self, sshfilebrowser):
        self._sshfilebrowser = sshfilebrowser

    def get_monitored_files(self):
        all_monitored_files = DBSession.query(MonitoredFile).all()

        for i, file in enumerate(all_monitored_files):
            all_monitored_files[i] = file.__dict__

            delete_keys = [key if key.startswith('_') else None for key in all_monitored_files[i].keys()]
            for key in delete_keys:
                if not key:
                    continue
                del all_monitored_files[i][key]
        return all_monitored_files

    def call_periodically(self, reason=None):
        print('test')

    def validate_files_in_place(self):
        allfiles = DBSession.query(MonitoredFile).all()
        log = logging.getLogger(__name__)
        # group them by folder
        grouped_files = {}
        for file in allfiles:
            if file.folder in grouped_files:
                grouped_files[file.folder].append((file, False))
            else:
                grouped_files[file.folder] = [(file, False)]
        # query the folder and evaluate whether files are existing or missing
        for (key, item) in grouped_files.items():
            required_files = [elem[0].filename for elem in item]

            output = self._sshfilebrowser.get_folder_content(key)
            if 'error' in output and output['error'] is not None:
                log.warning('Error occured during folder content retrieval: {0}'.format(output['error']))
                continue
            for r in output['lines']:
                if r['name'] in required_files:
                    ind = required_files.index(r['name'])
                    item[ind] = (item[ind][0], True)

        # filter missing files (TODO: make this more elegant)
        missing_files = []
        for (key, item) in grouped_files.items():
            for file in item:
                if not file[1]:
                    if key in missing_files:
                        missing_files.append(file[0].filename)
                    else:
                        missing_files = [file[0].filename]
        return missing_files


    def restore_directory_structure(self):
        log = logging.getLogger(__name__)
        log.error('not yet implemented')
        pass

