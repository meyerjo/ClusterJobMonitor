import logging
import re

import datetime


class SSHFileBrowser:

    def __init__(self, sshholder):
        self._ssh = sshholder

    def parse_ls_output(self, output):
        log = logging.getLogger(__name__)
        parsed = {}
        totalline = output[0]
        totalre = re.search('^total\s(\d+)', totalline)
        parsed['title'] = totalre.group(1)
        parsed['lines'] = []
        for line in output[1:]:
            line = line.rstrip('\n')
            linesplit = line.split(' ')
            linesplit = [c for c in linesplit if c]
            if len(linesplit) >= 8:
                tmp = dict(permission=linesplit[0], number_of_links=linesplit[1], owner=linesplit[2], group=linesplit[3],
                           filesize=linesplit[4], date=' '.join(linesplit[5:7]), name=linesplit[7], additional=linesplit[8:])
                parsed['lines'].append(tmp)
            else:
                log.info('Discarded line from ls output {0}'.format(linesplit))
        return parsed


    def get_folder_content(self, folder=None):
        if folder is None:
            folder = '.'
        cmd = 'cd {0}; pwd; ls -l -q -1 --time-style=long-iso'.format(folder)
        log = logging.getLogger(__name__)
        output = self._ssh.send_command(cmd)
        if output['error'] is not None:
            log.info('Get folder retrieval is stopping early: {0}'.format(output['error']))
            return output
        stderrstr = '\n'.join(output['stderr'])
        if re.search('bash: no such', stderrstr):
            return dict(error='Error in stderr: {0}'.format(stderrstr))
        if output['stdout']['error'] is not None:
            return output['stdout']

        stdout = output['stdout']['content']
        if len(stdout) < 2:
            print('---')
            return dict(error='Not enough lines returned')
        folder_after_cd = stdout[0].strip('\n')
        parsed = self.parse_ls_output(stdout[1:])
        parsed.update(dict(folder=folder_after_cd))
        return parsed

