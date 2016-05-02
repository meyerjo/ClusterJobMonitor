
# walltime - short, long, ultralong
# ppn -
# memory -
import logging
import os
import re
from argparse import ArgumentParser


class JobSubmitStatement():

    def __init__(self):
        self._config = dict()
        self._shorthandtimes = dict(tiny='00:10:00', small='00:30:00', middle='01:00:00', long='10:00:00', ultralong='01:00:00:00')
        for i in range(1, 24):
            self._shorthandtimes['{0}h'.format(i)] = '{0:02d}:00:00'.format(i)

    def set_config(self, config):
        log = logging.getLogger(__name__)
        if config['verbose']:
            log.info('Got the following settings: {0}'.format(config))
        self._config = config
        self._config['memory_per_proc'] = self._config['memory'] / self._config['ppn']

    def update_config_from_file(self):
        log = logging.getLogger(__name__)
        if self._config is not None:
            configfilename = self._config['configfile']
            if configfilename is None or configfilename == '':
                log.debug('No config file provided')
                return False
            if configfilename.endswith('.yaml'):
                try:
                    with open(configfilename) as yamlfile:
                        try:
                            import yaml
                            obj = yaml.safe_load(yamlfile.read())
                        except ImportError as e:
                            log.error('Error loading yaml and loading file: {0}'.format(str(e)))
                except BaseException as e:
                    log.error('Error parsing {0} with yaml: {1}'.format(configfilename, e))
                    return
            else:
                if not configfilename.endswith('.json'):
                    log.warning('Configfile does not end with yaml or json. Assuming it is json formatted anyways.')
                try:
                    with open(configfilename) as configfile:
                        import json
                        obj = json.loads(configfile.read())
                except BaseException as e:
                    log.warning('Error loading {0}: {1}'.format(configfilename, str(e)))
                    return
            if obj is not None:
                self._config.update(obj)
                self._config['memory_per_proc'] = self._config['memory'] / self._config['ppn']
        else:
            log.error('First call set_config')


    def _get_walltime(self):
        if 'walltime' in self._config:
            log = logging.getLogger(__name__)
            if re.match('^(\d{2}:){1,3}(\d{2})$', self._config['walltime']):
                return self._config['walltime']
            else:
                if self._config['walltime'] in self._shorthandtimes:
                    return self._shorthandtimes[self._config['walltime']]
                else:
                    log.warning('Returning: 03:00:00. Don''t recognize {0}, options are {1}'.format(self._config['walltime'], self._shorthandtimes.keys()))
                    return '03:00:00'
        else:
            return '03:00:00'


    def _get_resources(self):
        nodes = 'nodes={0}'.format(self._config['nodes'])
        ppn= 'ppn={0}'.format(self._config['ppn'])
        walltime = 'walltime={0}'.format(self._get_walltime())
        pmem = 'pmem={0}gb'.format(int(self._config['memory_per_proc']))

        return '-l {0}:{1},{2},{3}'.format(nodes, ppn, walltime, pmem)

    def _variablefile_to_variables(self, variablefilename):
        with open(variablefilename) as variablefile:
            variables = []
            lines = variablefile.readlines()
            lines = [line.rstrip('\n') for line in lines]
            for line in lines:
                variables.append(self._parse_single_variable(line))
        return variables

    def _json_parseable(self, candidatestr):
        """Validates whether the string can be parsed """
        try:
            import json
            obj = json.loads(candidatestr)
            return True
        except BaseException as e:
            log = logging.getLogger(__name__)
            log.error('Error parsing "{0}". Message: {1}'.format(candidatestr, str(e)))
            return False

    def _parse_single_variable(self, variable):
        """Generate single variable option for msub command"""
        if re.search('=', variable):
            # TODO: check if this is valid
           return '-v {0}'.format(variable)
        else:
            return '-v SCRIPT_FLAGS="{0}"'.format(variable)

    def _get_variables(self):
        variables = ['']
        log = logging.getLogger(__name__)
        if self._config['scriptvariables'] is not None and  self._config['scriptvariables'] != '':
            variables = []
            scriptvariables = self._config['scriptvariables']
            if os.path.exists(scriptvariables):
                log.debug('Scriptvariables is a filename. Going through linewise.')
                variables = self._variablefile_to_variables(scriptvariables)
            else:
                log.debug('Scriptvariables option is not a file. Interpreting it as a json string, which represents an array.')
                if self._json_parseable(scriptvariables):
                    varlist = None
                    try:
                        import json
                        varlist = json.loads(scriptvariables)
                    except ImportError as e:
                        log.warning('Problem parsing script-variables from json: {0}'.format(str(e)))

                    if isinstance(varlist, list):
                        for l in varlist:
                            variables.append(self._parse_single_variable(l))
                    else:
                        log.error('Varlist is not of type list: {0}'.format(type(varlist)))
                else:
                    log.warning('String is not parsable')
                    variables = [self._parse_single_variable(scriptvariables)]
        return variables

    def _get_mailsettings(self):
        log = logging.getLogger(__name__)
        if self._config['mailnotification']:
            if self._config['mailaddress'] is None or self._config['mailaddress'] == '':
                log.error('Mailnotifications are activated, but no mailaddress is provided. Going to ignore mail related settings')
                return ''
            # TODO: validate mail address
            if not re.search('^[abe]{1,3}$', args.mailnotification_settings):
                log.warning('Illegal mailnotification settings resetting it to default')
                self._config['mailnotification_settings'] = 'abe'
            return '-m {settings} -M {mail}'.format(**{'settings': self._config['mailnotification_settings'],
                                                       'mail': self._config['mailaddress']})
        else:
            return ''


    def make(self):
        log = logging.getLogger(__name__)
        if self._config is None or not isinstance(self._config, dict):
            log.error('First call set_config')
            return []

        queue = '-q {0}'.format(self._config['nodetype'])
        resources = self._get_resources()
        mailsettings = self._get_mailsettings()

        variables = self._get_variables()
        commands = []
        for variable in variables:
            command = 'msub {mailsettings} {queue} {resources} {scriptvariable} {scriptname}'.format(**{'queue': queue,
                                                                            'resources': resources,
                                                                            'mailsettings': mailsettings,
                                                                            'scriptname': self._config['scriptname'],
                                                                            'scriptvariable': variable})
            commands.append(command)
        return commands

if __name__ == '__main__':
    FORMAT = '%(asctime)-15s [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s'
    logging.basicConfig(format=FORMAT)
    log = logging.getLogger(__name__)

    parser = ArgumentParser(description='Run a job on the cluster. Note: If you provide an configfile this configfile always is higher ranked than the provided settings.')
    parser.add_argument('--nodetype', default='singlenode', help='Specify the node type')
    parser.add_argument('--memory', default=32, help='Overall memory necessary in gb', nargs='?', type=int )
    parser.add_argument('--ppn', default=8, help='Processors per node', nargs='?', type=int)
    parser.add_argument('--nodes', default=1, help='Number of nodes', nargs='?', type=int)
    parser.add_argument('--walltime', default='03:00:00', help='Runtime of the script', nargs='?', type=str)
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--mailnotification', action='store_true', default=False)
    parser.add_argument('--mailnotification_settings', default='abe', nargs='?')
    parser.add_argument('--mailaddress', type=str, nargs='?')
    parser.add_argument('-c', '--configfile', type=str, nargs='?')
    parser.add_argument('-t', '--test', action='store_true', help='Just test the execution. Don''t write to the commandline')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')

    parser.add_argument('scriptname', type=str, help='Name of the script which should get executed')
    parser.add_argument('scriptvariables', nargs='?', type=str, help='Filename or list of variables which are json encoded. '
                                                                     'Example for the latter: "[\\"var1\\", \\"var2\\"]"')

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    if not os.path.exists(args.scriptname):
        log.error('The script: {0} doesn''t exist'.format(args.scriptname))
        if args.test:
            log.warning('Usually script would stop here. Because the test mode is activated we don''t stop here.')
        else:
            exit(-1)

    dict_args = args.__dict__

    stmt = JobSubmitStatement()
    stmt.set_config(dict_args)
    stmt.update_config_from_file()
    cmds = stmt.make()
    if args.test:
        log.info('Would send the following commands to the commandline')
        for cmd in cmds:
            log.info(cmd)
    else:
        log.info('Sending commands to commandline')
        for cmd in cmds:
            os.system(cmd)
            log.info(cmd)
