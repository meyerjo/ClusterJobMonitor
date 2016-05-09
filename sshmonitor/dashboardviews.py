import datetime

import re
from pyramid.view import view_config

from sshmonitor.job_database_wrapper import JobDatabaseWrapper


class DashboardViews():

    def __init__(self, request):
        self._request = request
        self._projectname = 'Dashboard'
        self._jobarchive = JobDatabaseWrapper().job_archive()

    def get_statistics(self):
        permonth = dict()
        perhour = dict()
        perweekday = dict()
        for row in self._jobarchive:
            submissiontime = row['SubmissionTime']
            group = re.search('(\([^)]+\))', submissiontime)
            if group:
                submissiontime = group.group(1)[1:-1]
            dt = datetime.datetime.strptime(submissiontime, '%Y-%m-%d %H:%M:%S')
            year_month = str(dt.strftime('%Y-%m'))
            hour = str(dt.strftime('%H'))
            weekday = str(dt.strftime('%A'))

            perhour[hour] = 1 if hour not in perhour else perhour[hour] + 1
            permonth[year_month] = 1 if year_month not in permonth else permonth[year_month] + 1
            perweekday[weekday] = 1 if weekday not in perweekday else perweekday[weekday] + 1
        return permonth, perhour, perweekday


    @view_config(route_name='dashboard_statistics', renderer='json', match_param='fieldname=weekday')
    def weekday_statistics(self):
        permonth, perhour, perweekday = self.get_statistics()

        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        data = [dict(period=key, jobs=perweekday[key]) if key in perweekday else dict(period=key, jobs=0)
               for key in weekdays]
        overall_data = dict(
            element=self._request.matchdict['fieldname'],
            data=data,
            xkey=['period'],
            ykeys=['jobs'],
            labels=['Jobs'],
            hideHover='auto',
            resize=True
        )
        return dict(data=overall_data, charttype='bar')

    @view_config(route_name='dashboard_statistics',renderer='json', match_param='fieldname=jobs_per_hour')
    def jobs_per_hour_statistics(self):
        permonth, perhour, perweekday = self.get_statistics()
        data = []
        print(perhour)
        for i in range(0, 24):
            str_i = '{0:02d}'.format(i)
            if str_i in perhour:
                data.append(dict(period=str_i, jobs=perhour[str_i]))
            else:
                data.append(dict(period=str_i, jobs=0))

        overall_data = dict(
            element=self._request.matchdict['fieldname'],
            data=data,
            xkey=['period'],
            ykeys=['jobs'],
            labels=['Jobs'],
            hideHover='auto',
            resize=True
        )
        return dict(data=overall_data, charttype='bar')


    @view_config(route_name='dashboard_statistics', renderer='json')
    def dummy(self):
        try:
            print(self._request.params)
        except BaseException as e:
            print(e)
        return self._request.matchdict


    @view_config(route_name='dashboard', renderer='templates/job_dashboard.pt')
    def dashboard(self):
        permonth, perhour, perweekday = self.get_statistics()
        
        return {'project': self._projectname, 'content': [permonth]}
