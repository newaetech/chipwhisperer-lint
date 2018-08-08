# server.py
# ChipWhisperer-Lint server with RESTful API
#
# Usage:
# 
# GET /projects: get a list of all projects
# POST /projects/: start a new project
# 
# GET /projects/<id>: view one project
# PUT /projects/<id>: change settings for one project (or start analysis)
# DELETE /projects/<id>: remove project
#
# GET /results: get a list of all results
# 
# GET /results/<id>: get one test result

import interface

# Web server
from gevent import monkey
monkey.patch_all(thread=False, socket=False)
from flask import Flask, Blueprint, jsonify, abort, make_response, request

# CLI
import configparser
import getopt
import os
import sys

# Logging
import log     # Our custom rotating log file
import logging # Default logging system
import time
import traceback

   
aa_bp = Blueprint('aa_bp', __name__, template_folder='templates')
   
@aa_bp.route("/")
def index():
    return "Autoanalysis Web API"
    
@aa_bp.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error':'Bad request'})), 400
    
@aa_bp.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error':'Not found'}), 404)
    
@aa_bp.errorhandler(405)
def not_allowed(error):
    return make_response(jsonify({'error':'Not allowed'}), 405)
    
@aa_bp.errorhandler(500)
def internal_error(error):
    return make_response(jsonify({'error':'Internal error'}), 500)    
    
@aa_bp.after_request
def after_request(response):
    timestamp = time.strftime('[%Y-%m-%d %H:%M:%S]')
    log.log_message('%s %s %s %s %s %s' % (
        timestamp, request.remote_addr,request.method, 
        request.scheme, request.full_path, response.status))
    return response

@aa_bp.errorhandler(Exception)
def exceptions(e):
    tb = traceback.format_exc()
    print tb
    timestamp = time.strftime('[%Y-%m-%d %H:%M:%S]')
    log.log_message('%s Exception caught:\n%s' % (timestamp, tb))
    return make_response(jsonify({'error':'Internal error'}), 500)

    
def gen_inifile(fname):
    if os.path.exists(fname):
        print "warning: file %s already exists" % fname
        print "aborting..."
        sys.exit(1)
        
    print "Generating .ini file"
    config = configparser.ConfigParser()
    config['Paths'] = {}
    config['Paths']['log_file'] = 'log/server.log'
    config['Paths']['db_path'] = 'db'
    config['Options'] = {}
    config['Options']['random_id'] = 'True'
    print "Writing to %s..." % fname
    with open(fname, "w") as f:
        config.write(f)
    print "Done"
    print "Exiting..."
    sys.exit(0)
    
def load_inifile(ini_file):
    config = configparser.ConfigParser()
    config.read(ini_file)

    try:
        log_file = config['Paths']['log_file']
        db_path = config['Paths']['db_path']
        random_id = config.getboolean('Options', 'random_id')
        trace_path = config['Paths']['trace_path']
        configopt_path = config['Paths']['config_path']
    except configparser.NoOptionError as e: 
        print "error: missing option in %s" % ini_file
        print e.message
        sys.exit(2)
        
    return log_file, db_path, random_id, trace_path, configopt_path
    
def usage(exit_code):
    print "usage: python server.py [config_file]"
    print "SC-Lint server application"
    print ""
    print "Options:"
    print "  -h, --help   Display this help"
    print "  -i, --ini f  Generate a default .ini file f"
    print ""
    print "Arguments:"
    print "  config_file  File with server configuration"
    print ""
    print "Sample usage:"
    print "  python server.py server.ini"
    
    sys.exit(exit_code)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hi:", ["help", "ini="])
    except getopt.GetoptError:
        usage(2)
        
    for opt, arg in opts:
        if opt in ("h", "--help"):
            usage(0)
        elif opt in ("i", "--ini"):
            gen_inifile(arg)

    ini_file = 'server.ini'
        
    application = create_app(ini_file)
    
    # Run web server
    application.run(debug=False)

    # Tear down
    interface.close()
    
    
def create_app(config_file="server.ini"):

    #Check ini file for quick configuration
    if not os.path.exists(config_file):
        print "error: can't find ini file %s" % config_file
        usage(2)

    # Load settings from ini file
    log_file, db_path, random_id, trace_path, option_path = load_inifile(config_file)
    log.init_log(log_file)
    interface.init(db_path, random_id, trace_path, option_path)
    
    # Stop Werkzeug logging
    
    wz_log = logging.getLogger('werkzeug')
    wz_log.disabled = True

    application = Flask(__name__)
    application.register_blueprint(aa_bp)
    application.register_blueprint(interface.if_blueprint)
    
    return application

if __name__ == "__main__":
    main(sys.argv[1:])
