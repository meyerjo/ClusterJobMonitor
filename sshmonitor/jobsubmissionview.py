import logging

import datetime
import jsonpickle
import transaction
from pyramid.request import Request
from pyramid.view import view_config

from jobmanager.job_database_wrapper import JobDatabaseWrapper
from jobmanager.sshbasedjobmanager import SSHBasedJobManager
from models import DBSession
from models.ConfigurationModel import JobConfiguration
from ssh.run_clusterjob import JobSubmitStatement


class JobSubmission():

    def __init__(self, request):
        self._request = request

    def _reformat_parameters(self, config_objects):
        assert(isinstance(config_objects, dict))
        log = logging.getLogger(__name__)
        if 'pmem' in config_objects:
            config_objects['memory'] = config_objects['pmem']
            del config_objects['pmem']
        log.info(config_objects)
        config_objects['verbose'] = False
        config_objects['nodetype'] = 'singlenode'
        config_objects['mailnotification'] = False
        obj = jsonpickle.decode(config_objects['scriptname'])
        config_objects['scriptname'] = obj['scriptname']
        config_objects['path_to_script'] = obj['scriptpath']

        key_names_to_convert = ['memory', 'nodes', 'ppn']
        for key in key_names_to_convert:
            if key in config_objects:
                config_objects[key] = int(config_objects[key])

        if 'walltime' in config_objects:
            if config_objects['walltime'] == '':
                config_objects['walltime'] = '01:00:00'
        return config_objects

    def _generate_commands(self, config):
        log = logging.getLogger(__name__)
        try:
            stmt = JobSubmitStatement()
            stmt.set_config(config)
            cmds = stmt.make()
        except BaseException as e:
            log.error(str(e))
            return None
        try:
            log.info(cmds)
            cmds = ['cd {0}; {1}'.format(config['path_to_script'], cmd) for cmd in cmds]
            return cmds
        except BaseException as e:
            log.error(str(e))
            return None


    @view_config(route_name='send_job', renderer='json', request_method='POST', match_param='action=test')
    def send_job_test(self):
        log = logging.getLogger(__name__)
        log.info(self._request.params)
        try:
            config_objects = dict(self._request.params)
            config_objects = self._reformat_parameters(config_objects)
        except BaseException as e:
            log.error(str(e))
            return dict(error=str(e), commands=None)
        try:
            cmds = self._generate_commands(config_objects)
            return dict(error=None, commands=cmds)
        except BaseException as e:
            log.error(str(e))
            return dict(error=str(e), commands=None)

    @view_config(route_name='send_job', request_method='POST', match_param='action=send', request_param='requestresponse=json', renderer='json')
    def send_job_json(self):
        log = logging.getLogger(__name__)
        cmds = None
        # adopt the request parameter
        try:
            config_objects = dict(self._request.params)
            config_objects = self._reformat_parameters(config_objects)
        except BaseException as e:
            log.error(str(e))
            return dict(error=str(e), commands=None)
        # generate the commands
        try:
            cmds = self._generate_commands(config_objects)
        except BaseException as e:
            log.error(str(e))
            return dict(error=str(e), commands=None)
        if 'selectedcommands' in config_objects:
            from operator import itemgetter
            selected_ids = config_objects['selectedcommands']
            try:
                selected_ids = jsonpickle.decode(selected_ids)
            except BaseException as e:
                log.warning('Error during parsing of selected command ids {0}'.format(selected_ids))
                selected_ids = None
            if selected_ids is not None:
                if not selected_ids:
                    cmds = []
                elif min(selected_ids) >= 0 and max(selected_ids) < len(cmds):
                    cmds = itemgetter(*selected_ids)(cmds)
                else:
                    log.warning('Ignoring the selected-commands flag')
            else:
                log.warning('Ignoring the selected-commands flag')
        # TODO: send the commands
        for cmd in cmds:
            try:
                ssh_holder = self._request.registry.settings['ssh_holder']
                ssh_holder.send_command(cmd)
            except BaseException as e:
                log.error(str(e))
        # return the result
        return dict(error=None, commands=cmds)

    @view_config(route_name='send_job', request_method='POST', match_param='action=send')
    def send_job(self):
        log = logging.getLogger(__name__)
        log.info(self._request.matchdict)
        log.info(self._request.params)
        jobs = self.send_job_json()

        subreq = Request.blank(self._request.route_url('jobs'), POST={'error': 'Not yet implemented'})
        return self._request.invoke_subrequest(subreq)

    @view_config(route_name='send_job', renderer='json', request_method='GET', match_param='action=scripts')
    def script_names(self):
        job_archive = JobDatabaseWrapper.job_archive()
        job_names = []
        for job in job_archive:
            if 'JobName' in job and 'IWD' in job:
                if (job['JobName'], job['IWD']) not in job_names:
                    job_names.append((job['JobName'], job['IWD']))
        return job_names

    @view_config(route_name='send_job', renderer='json', request_method='POST')
    def send_job_dummy(self):
        return dict(error='Unknown request {0}'.format(str(self._request.matchdict)))

    @view_config(route_name='variable_environment', renderer='json', request_method='POST', match_param='action=save')
    def save_variable_environment(self):
        log = logging.getLogger(__name__)
        try:
            conf_name = self._request.params['name']
            conf_variable = self._request.params['data']
            job_name = self._request.params['scriptname']
            job_path = self._request.params['scriptpath']
            user_id = None
            with transaction.manager:
                # TODO: if the conf_name is already
                query = DBSession.query(JobConfiguration).filter(JobConfiguration.configuration_name == conf_name).first()
                if query is None:
                    DBSession.add(JobConfiguration(conf_name, job_name, job_path, conf_variable, user_id))
                else:
                    query.conf_variable = conf_variable
                DBSession.commit()
                return dict(error=None)
        except BaseException as e:
            log.error(str(e))
            raise e

    @view_config(route_name='variable_environment', renderer='json', request_method='POST', match_param='action=load')
    def load_variable_environment(self):
        log = logging.getLogger(__name__)
        try:
            with transaction.manager:
                query_result = DBSession.query(JobConfiguration.configuration_name, JobConfiguration.variable_set).all()
                query_result = [dict(zip(['job_name', 'variable_set'], q)) for q in query_result]
            query_result = [dict(job_name='New one', variable_set='{}'),] + query_result
        except BaseException as e:
            log.error(str(e))
            query_result = [dict(job_name='New one', variable_set='{}', create_time=str(datetime.datetime.now()))]
        return query_result
