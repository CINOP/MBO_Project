"""Provides some utilities widely used by other modules"""
import os


class ConfigDict(dict):
    ''''
    Modified dict class that handles some exceptions.
    '''
    def __init__(self, filename):
        self._filename = filename
        if not os.path.isfile(self._filename):
            try:
                open(self._filename, 'w').close()
            except IOError:
                raise IOError('Problem with the path')
            with open(self._filename) as fh:
                for line in fh:
                    line = line.rstrip()
                    key, value = line.split(',', 1)
                    dict.__setitem__(self, key, value)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        with open(self._filename, 'w') as fh:
            for key, val in self.items():
                fh.write('{0},{1}\n'.format(key, val))
