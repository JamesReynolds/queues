# -*- coding: utf-8 -*-
"""
Python netdata module to calculate queue service times
"""

from bases.FrameworkServices.UrlService import UrlService

import json

priority = 90000

ORDER = [
    'queues',
    'lengths',
    'service',
]

CHARTS = {
    'queues': {
        'options': [None, 'Arrival rate', 'Items per second', 'queues', 'rate', 'line'],
        'lines': [
            ['staging_count', 'staging', 'incremental'],
            ['plugin_count', 'plugin', 'incremental'],
            ['done_count', 'done', 'incremental'],
        ]
    },
    'lengths' : {
        'options' : [None, 'Queue length', 'Items', 'queues', 'length', 'line'],
        'lines' : [
            ['staging_length', 'staging', 'absolute'],
            ['plugin_length', 'plugin', 'absolute'],
        ]
    },
    'service' : {
        'options' : [None, 'Service time', 'Time', 'queues', 'time', 'line'],
        'lines' : [
            ['staging_time', 'staging', 'absolute'],
            ['plugin_time', 'plugin', 'absolute'],
        ]
    },
}

QMAPPING = {
    'staging' : 'upload',
    'plugin' : 'staged',
    'done' : 'done'
}

QORDER = ['staging', 'plugin', 'done']

class Service(UrlService):
    """
    This service reads from the counters end point and returns the maximum items
    running through each counter and the current length of each queue.
    """

    def __init__(self, configuration=None, name=None):
        UrlService.__init__(self, configuration=configuration, name=name)
        self.order = ORDER
        self.definitions = CHARTS
        self.allkeys = [['%s_count' % k, '%s_length' % k] for k in QORDER[:-1]]
        self.allkeys = [item for sublist in self.allkeys for item in sublist]
        self.previous = None
        self.averages = {k : 0 for k in self.allkeys}
        self.alpha = 1.0 / 60
        try:
            self.url = str(self.configuration['url'])
        except (KeyError, TypeError):
            self.url = "http://localhost/counters"

    def smooth(self, key, x_1):
        """
        Add the new value x_1 to the smoothed value averages[key] using our alpha constant
        """
        self.averages[key] = self.averages[key] * (1 - self.alpha) + x_1 * self.alpha
        return self.averages[key]

    def check(self):
        """
        Check whether the service is working
        See queues.conf.timeout parameter
        """
        return UrlService.check(self)

    def _get_data(self):
        """
        Attempt to find the data by processing the raw data
        """
        response = self._get_raw_data()
        decoded = json.loads(response)
        result = dict()

        ## Calculate simple values
        for key in QORDER:
            if not QMAPPING[key] in decoded:
                decoded[QMAPPING[key]] = 0
        for key, nextkey in zip(QORDER, QORDER[1:] + [None]):
            result['%s_count' % key] = decoded[QMAPPING[key]]
            if nextkey:
                result['%s_length' % key] = decoded[QMAPPING[key]] - decoded[QMAPPING[nextkey]]

        ## Make sure we have some form of previous value
        if self.previous is None:
            self.previous = result

        ## Calculate smoothed values
        for key in QORDER[:-1]:
            count = result['%s_count' % key] - self.previous['%s_count' % key]
            length = result['%s_length' % key]

            ## Use the previous value if we don't need an update
            timekey = '%s_time' % key
            result[timekey] = self.previous[timekey] if timekey in self.previous else 0

            ## Only update if there are values, otherwise we reduce numerical accuracy
            ## for no reason
            if count == 0 and length == 0:
                continue
            
            ## Smooth the values and save the result
            avg_count = self.smooth('%s_count' % key, count)
            avg_length = self.smooth('%s_length' % key, length)
            if avg_count > 0:
                result[timekey] = avg_length / avg_count / self.update_every

        ## Save our results
        self.previous = result
        return result
