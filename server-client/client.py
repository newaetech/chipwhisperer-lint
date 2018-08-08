# Client side for autoanalyzer 

import datetime
import getopt
import matplotlib.pyplot as plt
import numpy as np
import os
import requests
import string
import sys
import time
from yattag import Doc
from tqdm import tqdm
from collections import OrderedDict
import ConfigParser
import chipwhisperer.common.api.TraceManager as cwtm
from chipwhisperer.common.api.CWCoreAPI import CWCoreAPI
from chipwhisperer.capture.auxiliary.recordtriggerlength import RecordTriggerLength

ini_fname = 'client.ini'

def read_ini_file(ini_fname):
    if not os.path.exists(ini_fname):
        raise IOError('ini file %s not found' % ini_fname)
    config = ConfigParser.ConfigParser()
    config.read(ini_fname)
    
    ret = {}
    try:
        ret['server'] = config.get('Server', 'server_url')
        ret['ignore'] = config.get('Ignored Tests', 'ignore').splitlines()[1:]
        return ret
    except ConfigParser.NoOptionError as e:
        raise IOError('error: %s' % (ini_fname, e))

def check_server_up(server):
    try:
        r = requests.get(server, timeout=15.0)
    except Exception, e:
        print "error while connecting to server: %s" % str(e)
        return False
    return True
    
def print_status(uri, block):
    total_stages = None
    while True:
        r = requests.get(uri)
        if total_stages is None:
            total_stages = len(r.json()['project']['results'])
        remaining = int(r.json()['project']['remaining'])
        num_done = total_stages - remaining
        try:
            frac_done = 1.0 * num_done / total_stages
        except ZeroDivisionError:
            frac_done = 0.0
        
        num_blocks = 20
        blocks_done = int(num_blocks * frac_done)
        progress_bar = "[" +  "="*blocks_done + " "*(num_blocks-blocks_done) + "]"
        print "Analysis progress: %4d / %4d " % (num_done, total_stages) + progress_bar + "\r",
        if remaining == 0:
            break
        if not block:
            break
        time.sleep(1)
    print ""
    
    if block:
        print "Analysis complete"
        
def gen_report(uri, ofname, t, ignore_list, plot_all_graphs=False):
    name_list = []
    ttrace_list = []
    imax_list = []
    tmax_list = []
    graph_list = []
       
    r = requests.get(uri, timeout=1)
    res_list = r.json()['project']['results']
    
    cwp_uri = string.replace(uri, 'projects', 'cwprojects')
    metadata = requests.get(cwp_uri, timeout=1).json()['cwproject']
    
    img_path = os.path.splitext(ofname)[0] + "_files"
    img_path_short = os.path.basename(img_path)
    
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    
    for i in tqdm(range(len(res_list))):
        res_uri = res_list[i]
        try:
            r = requests.get(res_uri, timeout=5)
        except requests.exceptions.ReadTimeout:
            #Try again one last time...
            r = requests.get(res_uri, timeout=5)
            
        name = r.json()['result']['name']

        try:
            trace_comb = r.json()['result']['data']['trace_c']
        except KeyError:            
            break
        
        tabs = np.abs(trace_comb)
        imax = np.argmax(tabs)
        tmax = np.abs(tabs[imax])
        
        name_list.append(name)
        ttrace_list.append(tabs)
        imax_list.append(imax)
        tmax_list.append(tmax)
        
            
        if tmax > t or plot_all_graphs:
            t_limit = [t] * len(ttrace_list[-1])
            
            plt.plot(trace_comb)
            plt.plot(t_limit)
            plt.grid()
            
            img_file = os.path.join(img_path, "%d.png" % i)
            plt.savefig(img_file)
            plt.gcf().clear()
        else:
            img_file = None
            
        graph_list.append(img_file)
        
    doc = Doc()
    tag = doc.tag
    text = doc.text
    stag = doc.stag
    
    with tag('html'):
        with tag('head'):
            with tag('style', type="text/css"):
                text("""
tr.failed {background-color: rgba(255, 0, 0, 0.2);}
tr.passed {background-color: rgba(0, 255, 0, 0.2);}
tr.nodata {background-color: rgba(127, 127, 127, 0.2); }
tr.nofail {background-color: rgba(0, 0, 255, 0.2); }
tr.failed:hover { background: red; }
tr.passed:hover { background: green; }
tr.nofail:hover { background: blue; }
td a { 
    display: block; 
    border: 1px solid black;
    padding: 16px; 
}
                        """)
        
        with tag('body'):        
            with tag('h1'):
                text('Side-Channel Lint Test Report')
            text('Report generated at ' + str(datetime.datetime.now()))  
            
            with tag('h1'):
                text('Project Information')
                
            meta_list = [
                'Project Name: %s'      % metadata['project_name'],
                'Capture Timestamp: %s' % metadata['capture_time'],
                'Capture Setup: %s'     % metadata['notes'],
                'Trace Format: %s'      % metadata['trace_format'],
                'Number of Traces: %s'  % metadata['num_traces'],
                'Trace Length: %s'      % metadata['num_points'],
                'Sample Rate: %s'       % metadata['sample_rate'],
            ]
            for m in meta_list:
                text(m)
                stag('br')
                
            with tag('h1'):
                text('Test Results')
                
            with tag('table'):
                with tag('tr'):
                    with tag('th'):
                        text('Test Number')
                    with tag('th'):
                        text('Test Name')
                    with tag('th'):
                        text('Max T-Test')
                    with tag('th'):
                        text('Result')             
                for i in range(len(name_list)):
                    test_nofail = (name_list[i] in ignore_list)
                    test_zero = tmax_list[i] < 0.001
                    test_fail = tmax_list[i] > t
                    
                    if test_nofail:
                        tr_class = "nofail"
                    elif test_zero:
                        tr_class = "nodata"
                    elif test_fail:
                        tr_class = "failed"
                    else:
                        tr_class = "passed"
                    with tag('tr', klass="%s"%(tr_class)):
                        with tag('td'):
                            with tag('a', href='#%d'%(i+1)):
                                text(str(i+1))
                        with tag('td'):
                            with tag('a', href='#%d'%(i+1)):
                                text( name_list[i])
                        with tag('td'):
                            with tag('a', href='#%d'%(i+1)):
                                text(str(tmax_list[i]))
                        with tag('td'):
                            with tag('a', href='#%d'%(i+1)):
                                text("[FAIL]" if test_fail else "[PASS]")
            stag('hr')
                
            for i in range(len(name_list)):
                pass_str = "[FAIL]" if tmax_list[i] > t else "[PASS]"
            
                with tag('h1', id='%d'%(i+1)):
                    text('Test %d: %s' % (i+1, name_list[i]))
                text('Maximum t: %f @ %d %s' % (tmax_list[i], imax_list[i], pass_str))
                stag('br')                
                img_file = graph_list[i]
                if img_file:
                    stag('img', src=img_file)
                stag('hr')
        
    with open(ofname, "w+") as f:
        print >>f, doc.getvalue()
        
def gen_summary(server, ofname, t_fail, pid_list, ignore_list):
    # Leakages is a dictionary of:
    # leakage_name: [t_stat for each project]
    # t_stat = -1 if leakage test wasn't part of the project
    leakages = OrderedDict()
    min_time = []
    max_time = []
    proj_names = []
    
    # Use one session to avoid slowdown (making/breaking connections)
    sess = requests.Session()
    
    for i_pid in range(len(pid_list)):
        # Get project to find title/results URIs
        pid = pid_list[i_pid]
        print "Downloading results for PID %d" % pid
        proj_uri = server + '/projects/%d' % pid
        cwp_uri = server + '/cwprojects/%d' % pid
        summary_uri = server + '/summaries/%d' % pid
        
        r = sess.get(proj_uri, timeout=1)
        proj_names.append(r.json()['project']['title'])
        
        # Hack: get timing data here
        r = sess.get(cwp_uri, timeout = 1)
        cwp = r.json()['cwproject']['project_name']
        
        tm = cwtm.TraceManager()
        tm.loadProject(cwp)
        timing = tm.getAuxData(0, RecordTriggerLength.attrDictTriggerLength)['filedata']
        min_time.append(min(timing))
        max_time.append(max(timing))
        
        # TODO: make this timeout shorter if we can speed up the server
        r = sess.get(summary_uri, timeout=30)
        res_names = r.json()['summary']['names']
        res_tstats = r.json()['summary']['t_values']
        
        for i in range(len(res_names)):
            name = res_names[i]
            if name not in leakages:
                leakages[name] = [-1] * i_pid
            
            t_max = res_tstats[i]
            leakages[name].append(t_max)
            
        for l_type in leakages:
            if len(leakages[l_type]) <= i_pid:
                leakages[l_type].append(-1)
        

        

   
    # Generate document
    doc = Doc()
    tag = doc.tag
    text = doc.text
    stag = doc.stag
    asis = doc.asis
    
    with tag('html'):
        with tag('head'):
            with tag('style', type="text/css"):
                asis("""
                th {
                    vertical-align: bottom;
                    white-space:nowrap;
                }
                .rotated-text {
                    display: inline-block;
                    vertical-align: bottom;
                    
                    width: 1.5em;
                    line-height: 1.5;
                }
                                        
                .rotated-text > div {
                    display: inline-block;
                    white-space: nowrap;
                    transform: translate(0%, 100%) rotate(-45deg);
                    transform-origin: 0 0;
                    margin-bottom: 50%;
                    pointer-events: none;
                }

                .rotated-text > div:after {
                    content: "";
                    float: left;
                    margin-top: 70%;
                }

                td.failed {background-color: rgba(255, 0, 0, 0.2);}
                td.passed {background-color: rgba(0, 255, 0, 0.2);}
                td.nodata {background-color: rgba(127, 127, 127, 0.2); }
                td.nofail {background-color: rgba(0, 0, 255, 0.2); }
                td.failed:hover { background: red; }
                td.passed:hover { background: green; }
                td.nofail:hover { background: blue; }
                td { 
                    border: 1px solid black;
                    padding: 16px; 
                }
                """)
        
        with tag('body'):        
            with tag('h1'):
                text('ChipWhisperer-Lint Test Report')
            text('Report generated at ' + str(datetime.datetime.now()))  
                
            with tag('h1'):
                text('Test Results')
                
            with tag('table'):
                with tag('tr'):
                    with tag('th'):
                        text('Test Number')
                    with tag('th'):
                        text('Test Name')
                    for name in proj_names:
                        with tag('th'):
                            with tag('div', klass='rotated-text'):
                                with tag('div'):
                                    text(name)
                                    
                # Hack: add timing info
                with tag('tr'):
                    with tag('td'):
                        text('-')
                    with tag('td'):
                        text('Minimum Time')
                    for t in min_time:
                        with tag('td'):
                            text('%d' % t)
                with tag('tr'):
                    with tag('td'):
                        text('-')
                    with tag('td'):
                        text('Maximum Time')
                    for t in max_time:
                        with tag('td'):
                            text('%d' % t)
                    
                test_num = 1
                for leakage_type in leakages:
                    t_stats = leakages[leakage_type]
                    with tag('tr'):
                        with tag('td'):
                            text(str(test_num))
                        with tag('td'):
                            text(leakage_type)
                        for i in range(len(t_stats)):
                            test_missing = (t_stats[i] == -1)
                            test_zero = (t_stats[i] < 0.001)
                            test_nofail = (leakage_type in ignore_list)
                            test_fail = t_stats[i] > t_fail
                            
                            if test_missing or test_zero:
                                td_class = "nodata"
                            elif test_nofail:
                                td_class = "nofail"
                            elif test_fail:
                                td_class = "failed"
                            else:
                                td_class = "passed"
                            with tag('td', klass="%s"%(td_class)):
                                if test_missing:
                                    text("-")
                                else:
                                    text("%.3f" % t_stats[i])
                    test_num += 1
        
    with open(ofname, "w+") as f:
        print >>f, doc.getvalue()
    
def cmd_run(argv):
    # Get options
    block = False
    config_file = None
    cwproject_file = None
    proj_title = None
    thread_count = 3
    
    try:
        opts, args = getopt.getopt(argv, "bh", ["block", "config=", "cwproject=", "title=", "threads=", "help"])
    except getopt.GetoptError:
        usage(2)
    for opt, arg in opts:
        if opt in ("-b", "--block"):
            block = True
        elif opt in ("--title",):
            proj_title = arg
        elif opt in ("--threads",):
            thread_count = int(arg)
        elif opt in ("--config",):
            config_file = arg
        elif opt in ("--cwproject",):
            cwproject_file = arg
        elif opt in ("-h", "--help"):
            usage(0, 'run')
        else:
            print "error: unrecognized option %s %s" % (opt, arg)
            usage(2, 'run')
       
    try:
        ini_data = read_ini_file(ini_fname)
    except IOError as e:
        print "error: could not read ini file %s" % ini_fname
        print e
        usage(2, 'run')
        
    server = ini_data['server']
    
    # Validate
    # Check if files are provided
    if config_file is None:
        print "error: no config file provided"
        sys.exit(2)
        
    if cwproject_file is None:
        print "error: no project file provided"
        sys.exit(2)
        
    # If no title, give a default one
    if proj_title is None:
        proj_title = os.path.basename(cwproject_file)
        print "warning: no title provided"
        print "using %s as default" % proj_title
        
    if not check_server_up(server):
        print "error: could not connect to server %s" % server
        sys.exit(2)
        
    # Create project
    print "Creating project..."
    payload = {
        'cwproject':cwproject_file,
        'config':config_file,
        'num_threads':thread_count,
        'title':proj_title,
    }
    
    r = requests.post(server + '/projects', json=payload)
    
    uri = r.json()['project']['uri']
    print "Project created at %s" % uri
    
    # Run analysis
    print "Running analysis..."
    payload = {
        'running':True
    }
    r = requests.put(uri, json=payload)
    print "OK"
    
    # Poll status 
    i = 0
    while True:
        print "Waiting for setup" + '.'*i + ' '*(6-i) + '\r',
        
        r = requests.get(uri)
        status = r.json()['project']['status']
        if status.startswith('running') or status.startswith('finished') or status.startswith('failed'):
            break
        time.sleep(1)
        i = (i+1)%6
    print ''
    print "Setup complete, status: " + status
    
    # Continue waiting for finished status until done
    print_status(uri, block)
        
    sys.exit(0)

def cmd_status(argv):
    # Get options
    block = False
    try:
        opts, args = getopt.getopt(argv, "bh", ["block", "help"])
    except getopt.GetoptError:
        usage(2)
    for opt, arg in opts:
        if opt in ("-b", "--block"):
            block = True
        elif opt in ("-h", "--help"):
            usage(0, 'status')
        else:
            print "error: unrecognized option %s %s" % (opt, arg)
            usage(2, 'status')
            
    if len(args) < 1:
        print "error: no pid provided"
        usage(2, 'status')
    
    try:
        ini_data = read_ini_file(ini_fname)
    except IOError as e:
        print "error: could not read ini file %s" % ini_fname
        print e
        sys.exit(2)
        
    server = ini_data['server']
    pid = int(args[0])
    uri = '%s/projects/%d' % (server, pid)
    
    #if not check_server_up(uri):
    #    print "error: could not connect to uri %s" % uri
    #    sys.exit(2)
        
    # Continue waiting for finished status until done
    print_status(uri, block)
    sys.exit(0)
    
def cmd_result(argv):
    # Get options
    html_file = None
    t_thres = 3.0
    
    try:
        opts, args = getopt.getopt(argv, "ht:", ["help", "html="])
    except getopt.GetoptError:
        usage(2, 'result')
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(0, 'result')
        elif opt in ("--html",):
            html_file = arg
        elif opt in ("-t",):
            t_thres = float(arg)
        else:
            print "error: unrecognized option %s %s" % (opt, arg)
            usage(2, 'result')
            
    if len(args) < 1:
        print "error: no pid provided"
        usage(2, 'result')
            
    try:
        ini_data = read_ini_file(ini_fname)
    except IOError as e:
        print "error: could not read ini file %s" % ini_fname
        print e
        sys.exit(2)
        
    server = ini_data['server']
    pid = int(args[0])
    uri = '%s/projects/%d' % (server, pid)
    ignore_list = ini_data['ignore']
    
    #if not check_server_up(uri):
    #    print "error: could not connect to uri %s" % uri
    #    sys.exit(2)
            
    if html_file is None:
        print "warning: no results files given"
        
    if html_file is not None:
        gen_report(uri, html_file, t_thres, ignore_list)
        print "Wrote HTML report to file %s" % html_file
        
    sys.exit(0)
    
def cmd_summary(argv):
    # Get options
    html_file = None
    t_thres = 3.0
    
    try:
        opts, args = getopt.getopt(argv, "ht:", ["help", "html="])
    except getopt.GetoptError:
        usage(2, 'summary')
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(0, 'summary')
        elif opt in ("--html",):
            html_file = arg
        elif opt in ("-t",):
            t_thres = float(arg)
        else:
            print "error: unrecognized option %s %s" % (opt, arg)
            usage(2, 'summary')
            
    if len(args) < 1:
        print "error: no pid provided"
        usage(2, 'summary')
            
    try:
        ini_data = read_ini_file(ini_fname)
    except IOError as e:
        print "error: could not read ini file %s" % ini_fname
        print e
        sys.exit(2)
        
    server = ini_data['server']
    pid_list = [int(a) for a in args[0:]]
    ignore_list = ini_data['ignore']
    
    if not check_server_up(server):
        print "error: could not connect to uri %s" % uri
        sys.exit(2)
            
    if html_file is None:
        print "warning: no results files given"
        
    if html_file is not None:
        gen_summary(server, html_file, t_thres, pid_list, ignore_list)
        print "Wrote HTML report to file %s" % html_file
        
    sys.exit(0)
    
def usage(exit_code, cmd=None):
    if cmd == "run":
        print "usage: python client.py run [options]"
        print "Generate a new autoanalysis project and start running the analysis"
        print ""
        print "Options:"
        print "  -b, --block    Block until the analysis is finished"
        print "  --cwproject c  Analyze the traces from the ChipWhisperer project file c"
        print "  --config c     Use the autoanalyzer configuration file c"
        print "  --threads n    Use n threads for analysis (default: 4)"
        print "  --title t      Title the project t (default: cwproject filename)"
        print "  -h, --help     Display this help"
        print ""
        print "Sample usage:"
        print "  python client.py run --cwproject=xmega.cwp --config=config.cfg"
        
    elif cmd == "status":
        print "usage: python client.py status [options] <pid>"
        print "Check the status of a project"
        print ""
        print "Options:"
        print "  -b, --block    Block until the analysis is finished"
        print "  -h, --help     Display this help"
        print ""
        print "Required fields:"
        print "  <pid>          The ID of the running project"
        print ""
        print "Sample usage:"
        print "  python client.py status 14"
        
    elif cmd == "result":
        print "usage: python client.py result [options] <pid>"
        print "Download the results of a project"
        print ""
        print "Options:"
        print "  -h, --help     Display this help"
        print "  --html f       Save an HTML report to the file f"
        print "  -t n           Set the failure threshold to t=n (default: 3.0)"
        print ""
        print "Required fields:"
        print "  <pid>          The ID of the finished project"
        print ""
        print "Sample usage:"
        print "  python client.py result --html report.html 14"
        
    elif cmd == "summary":
        print "usage: python client.py summary <pids>"
        print "Generate a summary results page for a number of projects"
        print ""
        print "Options:"
        print "  -h, --help    Display this help"
        print "  --html f      Save an HTML report to the file f"
        print "  -t n           Set the failure threshold to t=n (default: 3.0)"
        print ""
        print "Required fields:"
        print "  <pids>         The IDs of the finished projects"
        print ""
        print "Sample usage:"
        print "  python client.py summary --html summary.html 14 15 16 17 18"
        
    else: # "help" or default
        print "usage: python client.py <command> [options] <server>"
        print ""
        print "Commands:"
        print "  help     Display a help screen about one of the commands"
        print "  run      Start a new analysis project"
        print "  status   Display the status of a project"
        print "  result   Download a project's results"
        print "  summary  Create a summary report for several projects"
        print ""
        print "For further instructions, try:"
        print "  python client.py help [command]"
        
    sys.exit(exit_code)
    

def main(argv):
    if len(argv) == 0:
        usage(2)
        
    cmd = argv[0]
    argv = argv[1:]
    if cmd in ['-h', '--help', 'help']:
        topic = None
        if len(argv) >= 1:
            topic = argv[0]
        usage(0, topic)
    elif cmd == 'run':
        cmd_run(argv)
    elif cmd == 'status':
        cmd_status(argv)
    elif cmd == 'result':
        cmd_result(argv)
    elif cmd == 'summary':
        cmd_summary(argv)
    else:
        usage(2)

    
if __name__ == "__main__":
    main(sys.argv[1:])
