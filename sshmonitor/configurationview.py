import re

import jsonpickle
from pyramid.view import view_config

from ssh.sshtest import SSHTest


class ConfigurationView:

    def __init__(self, request):
        self._request = request
        self._projectname = 'ClusterManagement'

    @view_config(route_name='sshconfiguration', renderer='templates/configurationeditor.pt', request_method='GET')
    def ssh_config(self):
        if 'projectname' in self._request.registry.settings:
            projectname = self._request.registry.settings['projectname']
        else:
            projectname = 'ClusterManagement'
        return dict(project=projectname, error=None, userobjects=dict())

    @view_config(route_name='sshconfiguration', renderer='templates/configurationeditor.pt', request_method='POST')
    def ssh_configuration_view(self):
        if 'projectname' in self._request.registry.settings:
            projectname = self._request.registry.settings['projectname']
        else:
            projectname = 'ClusterManagement'
        if (self._request.params.get('password') != self._request.params.get('password_repeat')):
            return dict(error='Passwords do not correspond', project=self._projectname, userobjects=dict())
        if self._request.params.get('servername') is '':
            return dict(error='Servername is not available', project=self._projectname, userobjects=dict())
        if self._request.params.get('username') is '':
            return dict(error='Username is not available', project=self._projectname, userobjects=dict())
        if self._request.params.get('portnumber') is '':
            portnumber = 22
        else:
            portnumber = int(self._request.params.get('portnumber'))
            if not re.search('[0-9]{1,6}', str(portnumber)):
                portnumber = 22

        obj = dict(server=self._request.params.get('servername'),
                   port=portnumber,
                   username=self._request.params.get('username'),
                   password=self._request.params.get('password'),
                   authentication='username_password')

        if self._request.params.get('submit_button') == 'submit':
            try:
                json = jsonpickle.encode(obj)
                with open(self._request.params['ssh.connection_params'], 'w+') as settings:
                    settings.write(json)
            except Exception as e:
                return dict(project=self._projectname, error=str(e), userobjects=obj)
        elif self._request.params.get('submit_button') == 'test':
            testresult = SSHTest.test(obj)
            if 'error' in testresult and testresult['error'] is not None:
                return dict(project=projectname, error=testresult['error'], userobjects=obj)
        else:
            return dict(project=projectname, error='Unknown submit button', userobjects=dict())
        return dict(project=projectname, error=None, userobjects=obj)
