"""
analysis.py

Multithreaded t-tests for ChipWhisperer projects
"""


import multiprocessing as mp
import multiprocessing.pool
import statsmodels.api as sm
import chipwhisperer.common.api.TraceManager as cwtm
import models
import os.path
import numpy as np
import re
import time
import traceback
import itertools
import types
import copy_reg
from tqdm import tqdm
import scipy.stats
import warnings

#TODO: Currently all the seperate threads have try...except wrapping them. It appears this might be the best way to actually get useful debug/info out of them, since they
#      are all in different threads. But it should have some nicer "stuff" around it

# This crazy copy_reg stuff comes from https://stackoverflow.com/questions/25156768/cant-pickle-type-instancemethod-using-pythons-multiprocessing-pool-apply-a
# It's required to use the pool.map multiprocessing step.
def _pickle_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)

copy_reg.pickle(types.MethodType, _pickle_method)

import shelve_db
from shelve_db import Project, Result

def update_result(res):
    """Find a result with this ID and update its status and data.
    """
    proj_list = shelve_db.get_projects()
    res_list  = shelve_db.get_results()
    res_list[res.id] = res
        
    try:
        proj = proj_list[res.pid]
        proj.remaining -= 1
        if proj.remaining == 0:
            proj.running = False
            proj.status = "finished"
        proj_list[res.pid] = proj
    except KeyError:
        raise KeyError("Error in result %d - could not find parent project %d" % (res.id, res.pid))
        
def load_data(proj_name):
    # Loads plaintext, key values, and traces for a project
    # Note: traces are loaded into memmap so we don't need to store them in RAM
    # (Helps other processes read this data)
    
    print "Opening trace manager..."
    tm = cwtm.TraceManager()
    tm.loadProject(proj_name)
    
    numtraces = tm.numTraces()
    tracelen = tm.numPoints()

    sample_pt = tm.getTextin(0)
    pt_len = np.shape(sample_pt)[0]
    
    sample_key = tm.getKnownKey(0)
    key_len = np.shape(sample_key)[0]
    
    pt  = np.empty((numtraces, pt_len), dtype=np.uint8)
    key = np.empty((numtraces, key_len), dtype=np.uint8)

    print "Loading data..." 
    for i in range(numtraces):
        pt[i] = tm.getTextin(i)
        key[i] = tm.getKnownKey(i)

    print "Traces loaded"    
    return [numtraces, tracelen, pt, key]

def load_config(config_fname):
    try:
        print "Loading file %s" % config_fname
        with open(config_fname, "r") as f:
            lines = f.read().splitlines()
        #print lines
        
        model = lines[0]
        num_groups = (len(lines) + 2) / 7
        name = []
        lt1  = []
        m1   = []
        lt2  = []
        m2   = []
        op   = []
        print "Number of tests found: %d" % num_groups
        
        for i in range(num_groups):
            lines_i = lines[7*i+1:7*i+7]
            name.append(lines_i[0])
            print "Loading test %s" % name[-1]
            lt1.append(lines_i[1])
            m1.append(int(lines_i[2], 16))
            lt2.append(lines_i[3])
            m2.append(int(lines_i[4], 16))
            
            op_text = re.split(" +", lines_i[5], 1)
            op_cmd = op_text[0]
            if len(op_text) > 1:
                op_arg = op_text[1]
            else:
                op_arg = ""
            op.append([op_cmd, op_arg])
        return [model, name, lt1, m1, lt2, m2, op]
    except:
        tb = traceback.format_exc()
        print tb
    
def calculate_HW(x):
    return bin(x).count("1")


def welch_ttest(group, traces):
    # Compute Welch's t-statistic at each point in time
    # Here, group[] must only contain booleans (True/False)
    try:
        traces_true = traces[np.where(np.array(group))]
        traces_false = traces[np.where(~np.array(group))]
        
        if len(traces_true) == 0:
            traces_true  = np.array([[np.nan for _ in range(len(traces[0]))]])
        if len(traces_false) == 0:
            traces_false = np.array([[np.nan for _ in range(len(traces[0]))]])
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ttrace = scipy.stats.ttest_ind(traces_true, traces_false, axis=0, equal_var=False).statistic
            
        return np.nan_to_num(ttrace) 
    except Exception as e:
        print traceback.format_exc()
    
def student_ttest(group, traces):
    try:
        group = np.array(group)
        S_x = np.sum(group)
        S_y = np.sum(traces, axis=0)
        S_xx = np.sum(group**2)
        S_yy = np.sum(traces**2, axis=0)
        S_xy = np.inner(np.transpose(traces), group)
        
        n = len(group)
        beta = (n*S_xy - S_x*S_y) / (n*S_xx - S_x**2)
        alpha = S_y/n - beta*S_x/n
        s_e2 = (n*S_yy - S_y**2 - beta**2 * (n*S_xx - S_x**2)) / n / (n-2)
        s_beta2 = n*s_e2 / (n*S_xx - S_x**2)
        
        t = beta / np.sqrt(s_beta2)
        return np.nan_to_num(t) 
    except Exception as e:
        print traceback.format_exc()
    
def worker_thread(group, numtraces, tracelen, proj_name, res):
    try:
        # Load data
        tm = cwtm.TraceManager()
        tm.loadProject(proj_name)
        traces = np.array([tm.getTrace(i) for i in range(numtraces)])
        ttrace = [np.zeros(tracelen) for _ in range(2)]
        split = numtraces/2
        
        # Count how many unique groups there are
        group_set = set(group)
        num_groups = len(group_set)
        
        # If we have 2 groups, set up a Welch t-test
        if num_groups == 2:
            true_val = group_set.pop()
            for ig in range(len(group)):
                group[ig] = (group[ig] == true_val)
            ttrace[0] = welch_ttest(group[:split], traces[:split])
            ttrace[1] = welch_ttest(group[split:], traces[split:])
        
        # Otherwise, default to the Student t-test
        else:
            ttrace[0] = student_ttest(group[:split], traces[:split])
            ttrace[1] = student_ttest(group[split:], traces[split:])
                
        trace_comb = np.zeros((len(ttrace[0])))
        for j in range(len(ttrace[0])):
            if ttrace[0][j] * ttrace[1][j] < 0:
                trace_comb[j] = 0
            elif ttrace[0][j] > 0:
                trace_comb[j] = min(ttrace[0][j], ttrace[1][j])
            else:
                trace_comb[j] = max(ttrace[0][j], ttrace[1][j])
        trace_comb = np.abs(trace_comb)
        
        # Copy data into results
        res.data = {
            'trace_0': list(ttrace[0]),
            'trace_1': list(ttrace[1]),
            'trace_c': list(trace_comb)
        }
        res.status = "finished"
        return res
    except Exception as e:
        print traceback.format_exc()
    
def start_analysis(arg_dict):
    """After performing the setup procedure, start the t-tests.
    
    This needs the following arguments:
    - pid (int): ID of the running project
    - res_list (list of results): List of result objects for this project
    - groups (num_config x numtraces array of int): List of groupings per t-test
    """
    try:
        proj_list = shelve_db.get_projects()
        res_list  = shelve_db.get_results()
        # Update the project status
        pid = arg_dict['pid']
        proj = proj_list[pid]
        status = arg_dict['status']
        proj.status = status
         
        # Check if setup ended successfully; if not, end early
        setup_ok = arg_dict['setup_ok']
        if not setup_ok:
            proj.running = False
            proj_list[pid] = proj
            return
             
        # Add new results objects and refer to them in project
        leak_names = arg_dict['leak_names']
        res_list = []
        for lname in leak_names:
            res = Result(proj.id, lname)
            res_list.append(res)
        rids = [r.id for r in res_list]
        proj.results = rids
        proj.remaining = len(rids)
        proj_list[pid] = proj

        # Run worker threads
        groups = arg_dict['groups']
        numtraces = arg_dict['numtraces']
        tracelen = arg_dict['tracelen']
        max_threads = arg_dict['max_threads']

        pool = mp.Pool(max_threads)
        for i in range(len(groups)):
            pool.apply_async(worker_thread, args=(groups[i], numtraces, tracelen, proj.cwproject, res_list[i]), callback=update_result)
        pool.close()
    except:
        print traceback.format_exc()
        raise    


def star_leakage(s):
    f = s[0]
    return f(s[1], s[2])

def setup_thread(proj, fname, config_fname, max_threads):
    try:
        print "Running setup..."
        ret = {'pid':proj.id}
        
        fname = os.path.normpath(fname)
        config_fname = os.path.normpath(config_fname)


        print fname
        # Check if files exist
        if not os.path.isfile(fname):
            ret['setup_ok'] = False
            ret['status'] = "failed (can't find CW project)"
            print 
            return ret
            
        if not os.path.isfile(config_fname):
            ret['setup_ok'] = False
            ret['status'] = "failed (can't find config file)"
            return ret
            
        print "Found files OK"
        print "Loading configuration file..."
           
        # Read config file
        [model_name, name, lt1, m1, lt2, m2, op] = load_config(config_fname)
        leakage_model = None
        for m in models.models:
            if m.name == model_name:
                leakage_model = m()
                break
        if leakage_model is None:
            ret['setup_ok'] = False
            ret['status'] = "failed (unrecognized leakage model %s)" % model_name
            return ret
        num_config = len(lt1)
        
        print "Config file loaded OK"
        
        # Run ciphers
        print "Loading data..."
        [numtraces, tracelen, pt, key] = load_data(fname)

        print "Calculating leakage..."   
        p = mp.Pool(8)
        c = p.map(star_leakage, itertools.izip(itertools.repeat(leakage_model.cipher), pt, key))

        print "Calculating groupings..."
        groups = []
                
        # For each result object:
        for idx in tqdm(range(num_config)):
            # Find internal states (masked)
            s1 = [c[i][lt1[idx]] & m1[idx] for i in range(numtraces)]
            s2 = [c[i][lt2[idx]] & m2[idx] for i in range(numtraces)]
            
            # Apply any operations
            if op[idx][0] == 'L':
                shft = int(op[idx][1])
                s2 = [s2[i] << shft for i in range(numtraces)]
            elif op[idx][0] == 'R':
                shft = int(op[idx][1])
                s2 = [s2[i] >> shft for i in range(numtraces)] 
            elif op[idx][0] == 'E':
                goal = int(op[idx][1], 0)
                s1 = [1 if s1[i] == goal else 0 for i in range(numtraces)]
                s2 = [1 if s2[i] == goal else 0 for i in range(numtraces)]

            # Find groups
            group = [calculate_HW(s1[i] ^ s2[i]) for i in range(numtraces)]
            groups.append(group)
            
        print "Setup complete"
        ret = {
            'setup_ok':True,
            'status':'running',
            'pid':proj.id,
            'leak_names':name,
            'groups':groups,
            'numtraces':numtraces,
            'tracelen':tracelen,
            'max_threads':max_threads,
        }
        return ret
    except:
        print traceback.format_exc()
        raise

class NoDaemonProcess(mp.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False
    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)

# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess


def start_setup(proj):
    """Start the analysis setup thread.
    
    Note that the values in the Project object are only read once here - any 
    changes during the analysis will have no effect.
    
    Arguments:
        proj (Project): the project to be used (in particular, the cwproject and
            config filenames and the number of threads are used to run the 
            analysis)
    """
    
    proj_list = shelve_db.get_projects()
    proj.status = "started"
    proj_list[proj.id] = proj
    cwp_fname = proj.cwproject
    cfg_fname = proj.config
    num_threads = proj.num_threads
    
    pool = MyPool(1)
    pool.apply_async(setup_thread, args=(proj, cwp_fname, cfg_fname, num_threads), callback=start_analysis)
    pool.close()

    
# Test code starts here
class DummyResult(object):
    """Dummy class to mock a Result() object.
    
    Only has data (dictionary) and status (string).
    """
    def __init__(self):
        self.data = {}
        self.status = None
        
def test_welch_ttest(plot=False):
    """Test the Welch T-Test analysis with some random data.
    
    Loads a small .cwp and runs a t-test with 2 groups.
    """
    # Load data
    proj_name = 'test_data/xmega-aes-small.cwp'
    tm = cwtm.TraceManager()
    tm.loadProject(proj_name)
    numtraces = tm.numTraces()
    tracelen = tm.numPoints()
    
    # Set up mock data
    group = [0, 1] * (numtraces/2)
    res = DummyResult()
    
    # Run analysis
    worker_thread(group, numtraces, tracelen, proj_name, res)
    ttrace = res.data['trace_c']
    
    # Optional: plot output - confirm max t ~ 2.3 
    if plot:
        import matplotlib.pyplot as plt
        plt.plot(res.data['trace_c'])
        plt.grid()
        plt.show()
    
    # Check output
    t_max = max(ttrace)
    if not (2.0 < t_max < 2.5):
        raise ValueError("Expected 2.0 < t_max < 2.5; got %f" % t_max)
    
    # If we get here, all is good
    print "Welch T-Test: [PASS]"
    
def test_1group_ttest(plot=False):
    """Make sure the ttest doesn't fail with one group
    
    Loads a small .cwp and runs a t-test with 1 group
    """
    # Load data
    proj_name = 'test_data/xmega-aes-small.cwp'
    tm = cwtm.TraceManager()
    tm.loadProject(proj_name)
    numtraces = tm.numTraces()
    tracelen = tm.numPoints()
    
    # Set up mock data
    group = [0] * (numtraces)
    res = DummyResult()
    
    # Run analysis
    worker_thread(group, numtraces, tracelen, proj_name, res)
    
    # Check output
    ttrace = res.data['trace_c']
    t_max = max(ttrace)
    #if t_max > 0:
    #    raise ValueError("Expected t_max = 0; got %f" % t_max)
    
    # Optional: plot output - confirm max t ~ 2.3 
    if plot:
        import matplotlib.pyplot as plt
        plt.plot(res.data['trace_c'])
        plt.grid()
        plt.show()
    
    # If we get here, all is good
    print "1 group T-Test: [PASS]"
    
def test_0dof_ttest(plot=False):
    """Make sure the ttest doesn't fail with a group with size 1
    """
    # Load data
    proj_name = 'test_data/xmega-aes-small.cwp'
    tm = cwtm.TraceManager()
    tm.loadProject(proj_name)
    numtraces = tm.numTraces()
    tracelen = tm.numPoints()
    
    # Set up mock data
    group = [0] * (numtraces)
    group[0] = 1
    res = DummyResult()
    
    # Run analysis
    worker_thread(group, numtraces, tracelen, proj_name, res)
    ttrace = res.data['trace_c']
    
    # Optional: plot output - confirm max t ~ 2.3 
    if plot:
        import matplotlib.pyplot as plt
        plt.plot(res.data['trace_c'])
        plt.grid()
        plt.show()
    
    # Check output
    t_max = max(ttrace)
    if t_max > 0:
        raise ValueError("Expected t_max = 0; got %f" % t_max)
    
    # If we get here, all is good
    print "0 DOF group T-Test: [PASS]"

if __name__ == "__main__":
    tests = [
        test_welch_ttest,
        test_1group_ttest,
        test_0dof_ttest,
    ]
    
    from timeit import default_timer as timer
    for t in tests:
        start = timer()
        t()
        end = timer()
        print(end - start)