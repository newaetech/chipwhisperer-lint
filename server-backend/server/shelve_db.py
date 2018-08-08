"""
shelve_db.py

Data structures and classes for working projects and results, including 
persistent access through a database
"""

import os
import random
random.seed()
import shelve

projects = results = None
# TODO: get this from command line
randomID = False

default_max_id = 2**32
default_last_id = 0

class ListStore(object):
    """A ListStore is a dictionary with extra utilities for saving objects
    to a Shelved database.
    
    Internally, the ListStore uses one dictionary with the following entries:
        _data['max_id']    = [int]
        _data['last_id']   = [int]
        _data['123']       = (item with ID 123)
    This is done to coordinate better with Shelve's data structures - all of
    these values are saved to disk via Shelve.
        
    Attributes:
        items (dict): A dictionary with the stored items. Access like items[id].
        max_id (int): For random ID generation, the maximum possible ID number.
        last_id (int): For sequential ID generation, the previous sequential ID.
    """
    
    def __init__(self, db_fname, max_id = None, last_id = None):
        """Load the database and check that all necessary keys exist
        
        Arguments:
            db_fname (string): name of Shelve DB file
            max_id (int): Max ID for random ID generation. If None, loads from 
                Shelve file or uses default value (2^32)
            last_id (int): Previous ID for sequential ID generation. If None, 
                loads from Shelve file
        """
        
        self.in_mem = False
        
        # Make sure the path exists before we try to access it
        if db_fname is None:
            self.in_mem = True
            
            #Fallback to in-memory
            print "WARNING: Falling back to in-memory db"
            self._data = {}
            if max_id is None:
                self._data['max_id'] = default_max_id
            else:
                self._data['max_id'] = max_id
            if last_id is None:
                self._data['last_id'] = default_last_id
            else:
                self._data['last_id'] = last_id
            
        else:
            
            dirname = os.path.dirname(db_fname)
            if not os.path.exists(dirname):
                os.mkdir(dirname)
                
            # Possible cases:
            # - File does not exist: make it
            if not os.path.exists(db_fname):
                self._data = shelve.open(db_fname)
                if max_id is None:
                    self._data['max_id'] = default_max_id
                else:
                    self._data['max_id'] = max_id
                if last_id is None:
                    self._data['last_id'] = default_last_id
                else:
                    self._data['last_id'] = last_id
                    
            else:
                # - File does exist but is missing necessary keys: exit
                self._data = shelve.open(db_fname)
                if 'max_id' not in self._data or 'last_id' not in self._data:
                    print "error in ListStore(): max_id/last_id missing from db file"
                    raise KeyError('max_id/last_id missing from file %s' % db_fname)
            
                # - File does exist and has necessary keys: load data
                if max_id is not None:
                    self._data['max_id'] = max_id
                if last_id is not None:
                    self._data['last_id'] = last_id
            self.sync()
            
            
    def sync(self):
        if self.in_mem is False:
            self._data
            
    @property
    def max_id(self):
        return self._data['max_id']
        
    @property
    def last_id(self):
        return self._data['last_id']
        
    @last_id.setter
    def last_id(self, value):
        if not isinstance(value, (long, int)): 
            raise TypeError('ID %s is not an integer' % value)
        self._data['last_id'] = value
        self.sync()
        
    def next_id(self, random_id=randomID):
        """Returns the next ID to be used.
        """
        if random_id:
            while True:
                id = random.randint(0, self.max_id-1)
                if str(id) not in self._data:
                    return id
        else:
            while True:
                self.last_id += 1
                if str(self.last_id) not in self._data:
                    return self.last_id
        
    def __getitem__(self, id):
        if not isinstance(id, (long, int)):
            raise TypeError("ID %s is not an integer" % id)
        k = str(id)
        if k not in self._data:
            raise KeyError("ID %d is not in list" % id)
        return self._data[k]
    
    def __setitem__(self, id, value):
        if not isinstance(id, (long, int)):
            raise TypeError("ID %s is not an integer" % id)
        k = str(id)
        self._data[k] = value
        self.sync()
            
    def __delitem__(self, id):
        if not isinstance(id, (long, int)):
            raise TypeError("ID %s is not an integer" % id)
        k = str(id)
        if k not in self._data:
            raise KeyError("ID %d is not in list" % id)
        del self._data[k]
        self.sync()
        
    def keys(self):
        klist = self._data.keys()
        ret = [int(k) for k in klist if k.isdigit()]
        return ret
        
    def close(self):
        self._data.close()

class Project(object):
    """A project object describes a single set of tests.
    
    The read-only attributes in this class can't be changed from the client 
    (ie: the POST/PUT methods don't touch them)
    
    Attributes:
        id (int, read-only): A unique identifier for each project
        cwproject (string): Server-side path to ChipWhisperer project
        config (string): Server-side path to analysis config file
        num_threads (int): Maximum number of worker threads
        remaining (int): Number of unfinished results
        running (bool): Whether the results are currently being computed
        results (list of int, read-only): List of t-test result IDs associated
            with this project
        status (string, read-only): current project state
    """
    
    def __init__(self, cwproject='', config='', num_threads=1, title=''):
        self.id = projects.next_id()
        
        self.cwproject = cwproject
        self.config = config
        self.num_threads = num_threads
        self.title = title
        
        self.remaining = 0
        self.running = False
        self.results = []
        self.status = ''
        
        projects[self.id] = self  

class Result(object):
    """A result object describes the output of a single t-test.
    
    This structure is read-only for clients - no POST/PUT methods are 
    implemented, so there is no way to change these values.
    
    Attributes (all read-only):
        id (int): Unique ID for this result set
        pid (int): ID of parent project
        name (string): Name of test for this result
        status (string): Current state of this result, such as "not started", 
            "in progress", or "finished"
        data (dict): The output of the t-test
            trace_0 (list of floats): T-test trace for half of traces
            trace_1 (list of floats): T-test trace for other half of traces
            trace_c (list of floats): Combined t-test values        
    """
    
    def __init__(self, pid=0, name=''):
        self.id = results.next_id()
        self.pid = pid
        self.name = name
        self.status = ''
        self.data = {}
        
        results[self.id] = self

def open_db(proj_fname, res_fname):
    global projects, results
    
    print "Opening database connections..."
    projects = ListStore(proj_fname)
    results = ListStore(res_fname)
    print "Database loaded"
    
def close_db():
    print "Closing database connections..."
    projects.close()
    results.close()        
    print "Database closed"
    
def get_projects():
    return projects
    
def get_results():
    return results
    
def update_projects():
    """Debugging function: take all projects and add some attributes
    """
    import os
    fname = 'db/projects.db'
    ls = ListStore(fname)
    for k in ls.keys():
        proj = ls[k]
        title = os.path.basename(proj.cwproject)
        proj.title = title
        ls[k] = proj

def test_liststore():
    fname = 'db/test.db'
    ls = ListStore(fname)
    for i in range(10):
        id = ls.next_id(True)
        ls[id] = i
    print ls.keys()
    
if __name__ == "__main__":
    update_projects()
    #test_liststore()