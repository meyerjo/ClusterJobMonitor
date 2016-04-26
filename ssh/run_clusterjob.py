
# walltime - short, long, ultralong
# ppn -
# memory -
import logging
import re
from argparse import ArgumentParser

class JobSubmitStatement():

    def __init__(self):
        self._config = dict()
        self._shorthandtimes = dict(tiny='00:10:00', small='00:30:00', middle='01:00:00', long='10:00:00', ultralong='01:00:00:00')
        for i in range(1, 24):
            self._shorthandtimes['{0}h'.format(i)] = '{0:02d}:00:00'.format(i)

    def set_config(self, config):
        self._config = config

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
        pmem = 'pmem={0}gb'.format(int(self._config['memory_per_node']))

        return '-l {0}:{1},{2},{3}'.format(nodes, ppn, walltime, pmem)

    def make(self):
        log = logging.getLogger(__name__)

        #  msub -q singlenode -m abe -M johannes.meyer@posteo.de -l nodes=1:ppn=8,walltime=00:15:00,pmem=4000mb -v SCRIPT_FLAGS="$trialperson" $2
        queue = '-q {0}'.format(self._config['nodetype'])
        resources = self._get_resources()

        if self._config['mailnotification']:
            log.info('not yet implemented')


        command = 'msub {queue} {resources}'.format(**{'queue': queue, 'resources': resources})
        return [command]

if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(levelname)s %(funcName)s %(lineno)d %(message)s'
    logging.basicConfig(format=FORMAT)
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    parser = ArgumentParser(description='Run a job on the cluster')
    parser.add_argument('--nodetype', default='singlenode', help='Specify the node type')
    parser.add_argument('--memory', default=32, help='Overall memory necessary in gb', nargs='?', type=int )
    parser.add_argument('--ppn', default=8, help='Processors per node', nargs='?', type=int)
    parser.add_argument('--nodes', default=1, help='Number of nodes', nargs='?', type=int)
    parser.add_argument('--walltime', default='03:00:00', help='Runtime of the script', nargs='?', type=str)
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--mailnotification', action='store_true', default=False)
    parser.add_argument('--mailnotification_settings', default='abe', nargs='?')
    parser.add_argument('--mailaddress', type=str, nargs='?')
    parser.add_argument('-t', '--test', action='store_true', help='Just test the execution. Don''t write to the commandline')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')

    parser.add_argument('scriptname', type=str, help='Name of the script which should get executed')
    parser.add_argument('scriptflags', nargs='?', type=str, help='Filename or list of trialpersons which should get applied')
    args = parser.parse_args()

    if args.mailnotification and args.mailaddress == '':
        log.error('If you want to use mail notification, you have to add a mail address')
        args.mailnotification = False

    dict_args = args.__dict__
    dict_args['memory_per_node'] =args.memory / args.ppn

    stmt = JobSubmitStatement()
    stmt.set_config(dict_args)
    cmds = stmt.make()
    if args.test:
        log.info('Would send the following commands to the commandline')
        for cmd in cmds:
            log.info(cmd)
    else:
        log.info('Sending commands to commandline')
        for cmd in cmds:
            log.info(cmd)



