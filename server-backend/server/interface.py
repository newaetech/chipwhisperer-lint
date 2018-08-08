"""
interface.py

Flask routing to control project/results
"""

from flask import Blueprint, jsonify, abort, make_response, request, url_for
from shelve_db import Project, Result
import shelve_db
import analysis
import os
import chipwhisperer.common.api.TraceManager as cwtm
from tqdm import *

if_blueprint = Blueprint('interface', __name__)

randomID = False

tpath = '.'
cpath = '.'

def init(db_path, rid, trace_path, config_path):
    global randomID
    randomID = rid
    
    projects_fname = os.path.join(db_path, 'projects.db')
    results_fname  = os.path.join(db_path, 'results.db')
    shelve_db.open_db(projects_fname, results_fname)
    #shelve_db.open_db(None, None)
    
    globals()['tpath'] = trace_path
    globals()['cpath'] = config_path
    
def close():
    shelve_db.close_db()
  
def get_public_project(project):
    """Produce a public JSON representation of this project.
    
    Convert all private IDs into URIs, then put all attributes into a dict.
    """
    ret = {
        'uri':url_for('interface.get_project', pid=project.id, _external=True),
        'cwproject':project.cwproject,
        'config':project.config,
        'remaining':project.remaining,
        'running':project.running,
        'results':[url_for('interface.get_result', rid=r, _external=True) for r in project.results],
        'status':project.status,
        'title':project.title,
    }
    return ret
    
def get_public_project_short(project):
    """Produce a short-form version of the project. 
    Useful for displaying many projects."""
    
    ret = {        
        'uri':url_for('interface.get_project', pid=project.id, _external=True),
        'cwproject':project.cwproject,
        'config':project.config,
        'status':project.status,
        'title':project.title,
    }
    return ret
    
def get_public_result(result):
    """Produce a public JSON representation of this result.
    
    Convert all private IDs into URIs, then put all attributes into a dict.
    """
    ret = {
        'uri':url_for('interface.get_result', rid=result.id, _external=True),
        'project_uri':url_for('interface.get_project', pid=result.pid, _external=True),
        'name':result.name,
        'status':result.status,
        'data':result.data
    }
    return ret
    
def get_public_result_short(result):
    """Produce a short-form version of the result. 
    Useful for displaying many results."""
    ret = {
        'uri':url_for('interface.get_result', rid=result.id, _external=True),
        'project_uri':url_for('interface.get_project', pid=result.pid, _external=True),
        'name':result.name,
        'status':result.status,
    }
    return ret
    
def get_cwproject_summary(fname):
    """Produce a JSON summary of a ChipWhisperer project.
    
    TODO: This is a bit of a hack for now - really we should check more than 
    one segment to get a range of results"""
    # Assume that project is readable - upstairs will catch the exceptions
    tm = cwtm.TraceManager()
    tm.loadProject(fname)
    cfg = tm.getSegment(0).config
    
    ret = {
        'project_name': fname,
        'capture_time': cfg.attr('date'),
        'num_traces':   cfg.attr('numTraces'),
        'num_points':   cfg.attr('numPoints'),
        'trace_format': cfg.attr('format'),
        'notes':        cfg.attr('notes'),
        'sample_rate':  cfg.attr('scopeSampleRate'),
    }
    return ret

@if_blueprint.route("/projects", methods=["GET"])
def get_projects():
    proj_list = shelve_db.get_projects()
    ret = [get_public_project_short(proj_list[k]) for k in proj_list.keys()]
    return jsonify({"projects": ret})
    
@if_blueprint.route("/projects/<int:pid>", methods=["GET"])
def get_project(pid):
    try:
        proj_list = shelve_db.get_projects()
        p = proj_list[pid]
        return jsonify({'project': get_public_project(p)})
    except KeyError:
        abort(404)
    
@if_blueprint.route("/projects", methods=["POST"])
def create_project():
    if not request.json or \
       not 'cwproject' in request.json or \
       not 'config' in request.json or \
       not 'num_threads' in request.json or \
       not 'title' in request.json:
        abort(400)
    
    cwproject = request.json['cwproject']
    config = request.json['config']
    
    cwproject = os.path.join(tpath, cwproject)
    config = os.path.join(cpath, config)
    
    #Assume we are going into directory    
    
    proj = Project(
        cwproject=cwproject,
        config=config,
        num_threads=request.json['num_threads'],
        title=request.json['title'],
    )
    
    return jsonify({'project':get_public_project(proj)}), 201

@if_blueprint.route("/projects/<int:pid>", methods=["PUT"])
def update_project(pid):
    try:
        proj_list = shelve_db.get_projects()
        p = proj_list[pid]
    except KeyError:
        abort(404)
        
    if not request.json:
        abort(400)
        
    # TODO: don't allow files to be changed when running
    vars = [
        {'name':'cwproject', 'type':basestring},
        {'name':'config', 'type':basestring},
        {'name':'title', 'type':basestring},
        {'name':'running', 'type':bool}
    ]
        
    for v in vars:
        if v['name'] in request.json and not isinstance(request.json[v['name']], v['type']):
            abort(400)

    for v in vars:
        setattr(p, v['name'], request.json.get(v['name'], getattr(p, v['name'])))
        
    proj_list[pid] = p
    
    if p.running:
        analysis.start_setup(p)

    return jsonify({"project":get_public_project(p)})
    
@if_blueprint.route("/projects/<int:pid>", methods=["DELETE"])
def delete_project(pid):
    try:
        proj_list = shelve_db.get_projects()
        del proj_list[pid]
        return jsonify({'result': True})
    except KeyError:
        abort(404)

@if_blueprint.route("/results", methods=["GET"])
def get_results():
    res_list = shelve_db.get_results()
    return jsonify({"results": [get_public_result_short(res_list[k]) for k in res_list.keys()]})
    
@if_blueprint.route("/results/<int:rid>", methods=["GET"])
def get_result(rid):
    try:
        res_list = shelve_db.get_results()
        r = res_list[rid]
        return jsonify({'result': get_public_result(r)})
    except KeyError:
        abort(404)
        
@if_blueprint.route("/cwprojects/<int:pid>", methods=["GET"])
def get_cwproject(pid):
    try:
        proj_list = shelve_db.get_projects()
        p = proj_list[pid]
        fname = p.cwproject
        if not os.path.isfile(fname):
            abort(404)
        return jsonify({"cwproject": get_cwproject_summary(fname)})
    except KeyError:
        abort(404)
        
@if_blueprint.route("/summaries/<int:pid>", methods=["GET"])
def get_summary(pid):
    try:
        proj_list = shelve_db.get_projects()
        res_list = shelve_db.get_results()
        p = proj_list[pid]
        
        test_names = [''] * len(p.results)
        test_results = [0] * len(p.results)
        for i in tqdm(range(len(p.results))):
            rid = p.results[i]
            # TODO: this loop is pretty slow.
            # This line is the cause - hopefully switching from Shelve to SQL
            # will fix it. Until then we can get around 20 it/s
            r_i = res_list[rid]
            t_max = max(r_i.data['trace_c'])
            test_names[i] = r_i.name
            test_results[i] = t_max
        ret = {'names': test_names, 't_values': test_results}
        return jsonify({'summary': ret})
    except KeyError:
        abort(404)