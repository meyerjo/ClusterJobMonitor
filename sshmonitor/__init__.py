import logging
import os

import jsonpickle
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from models import initialize_sql
from ssh.ssh_connectionholder import SSHConnectionHolder
from ssh.sshfilebrowser import SSHFileBrowser
from sshmonitor.filemonitor import FileMonitor
from sshmonitor.jobmanager import JobManager
from sshmonitor.sshbasedjobmanager import SSHBasedJobManager


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
    logging.basicConfig(format=FORMAT)

    log = logging.getLogger(__name__)
    if 'ssh.connection_params' in settings:
        if not os.path.exists(settings['ssh.connection_params']):
            log.error('File containing SSH connection parameters does not exist')
            exit(2)
        with open(settings['ssh.connection_params']) as f:
            ssh_param = jsonpickle.decode(f.read())
    else:
        raise BaseException('SSH Connection parameters file is not specified. See README')

    config = Configurator(settings=settings)
    config.scan('models') # the "important" line
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)

    config.include('pyramid_chameleon')
    # config.registry.settings['ssh_holder'] = SSHConnectionHolder(ssh_param)

    # fm = FileMonitor(SSHFileBrowser(config.registry.settings['ssh_holder']))
    # print(fm.get_monitored_files())
    # print(fm.validate_files_in_place())

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('job_details', '/jobdetails/{jobid}')
    config.add_route('cancel_job', '/canceljob/{jobid}')
    config.add_route('joboutput', '/joboutput/{jobid}')
    config.add_route('jobarchive', '/archive')
    config.add_route('jobarchive_config', '/archive/config')

    config.add_route('dashboard', '/dashboard')
    config.add_route('dashboard_statistics', '/dashboard/{fieldname}/json')

    config.add_route('filemonitor', '/filemonitor')
    config.add_route('filemonitor_editor', '/filemonitor/{modus}/{options}')
    config.add_route('filebrowser', '/browser')

    config.add_route('sshconfiguration', '/sshconfiguration')
    config.add_route('jobs', '/')
    config.scan()
    return config.make_wsgi_app()
