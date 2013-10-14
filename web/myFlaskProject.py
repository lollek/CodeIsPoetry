#! /usr/bin/env python3
# -*- coding: utf-8 -*- 

import os
import sys
import re
import signal

try:
    from flask import Flask, url_for, render_template, request
except:
    print("Unable to import flask. Did you maybe forget to initialize venv?")
    sys.exit()

import data

def static_dir(): return os.path.dirname(os.path.abspath(__file__))
def tmpl_dir(): return os.path.join(static_dir(), 'templates')

def main():
    """ Main """
    def usage(): print("Usage: %s start|stop" % sys.argv[0])
    
    if len(sys.argv) != 2:
        usage()
        return

    if sys.argv[1] == "start":
        print("Starting myFlaskProject")

        # Start server on a fork:
        pid = os.fork() 
        if not pid: 
            sys.stdout = sys.stderr = open(os.path.join(static_dir(), 
                                            "../log"), 'a')
            print("Start signal received")
            app.run(host="0.0.0.0")

        # Save pid:
        with open(os.path.join(static_dir(), "../pid"), 'w') as f:
            print("%d" % pid, file=f)

    elif sys.argv[1] == "stop":
        print("Killing myFlaskProject")
        with open(os.path.join(static_dir(), "../log"), 'a') as f:
            print("Stop signal received", file=f)

        # Kill pid in pidfile, then remove it:
        try:
            with open(os.path.join(static_dir(), "../pid"), 'r') as f:
                os.kill(int(f.read().strip()), signal.SIGTERM)
            os.remove(os.path.join(static_dir(), "../pid"))
        except BaseException as e:
            print("Failed to kill process. Reason: %s" % str(e),
                    "If it's still running, please kill it manually",
                    sep="\n")
            return
        print("Done")
            
    else:
        usage()
        return

app = Flask(__name__, template_folder=tmpl_dir(), static_folder=static_dir())

@app.route("/")
def main_page():
    """
    Returns main page of the website, address "/"
    """
    return render_template("main.html", data=data.load("data.json"), 
                            info=data.load("main.json"))
    
@app.route("/list")
def project_list():
    """
    Returns a list of projects on the website, address "/list"
    """
    appdata = data.load("data.json")
    project_count = data.get_project_count(appdata)
    return render_template("list.html", data=appdata, 
                            count=project_count, info=data.load("main.json"))
    
@app.route("/techniques")
def project_tech():
    """
    Returns a list of techniques we have used on the website, 
    address "/techniques".
    Each technique also lists projects where the technique was used.
    """
    techniques = data.get_technique_stats(data.load("data.json"))
    return render_template("tech.html", techs=techniques, 
                            info=data.load("main.json")) 
    
@app.route("/project/<int:id>")
def project_single(id):
    """
    Returns a page with description for a single project, 
    adress "/project/<project_id>".
    """
    single_project = data.get_project(data.load("data.json"), id)
    return render_template("single.html", data=single_project)

@app.route("/searchform")
def search_form():
    """ 
    Returns a page with search form with all the available search options
    """
    appdata = data.load("data.json")
    techniques = data.get_technique_stats(appdata)
    info_json = data.load("main.json")
    return render_template("searchform.html", data=appdata, 
                            techs=techniques, info=info_json)
    
@app.route("/search", methods=['POST'])
def search_results():
    """
    Sanitizes the search string, 
    counts objects in search results and returns search results page. 
    sort_order=request.form['sort'], 
    search_fields=fields, 
    techniques=request.form['techfield']
    """
    appdata = data.load("data.json")
    sanitized_search = re.sub('[^a-zA-Z0-9\.]', "", request.form['key'])
    techs = request.form.getlist('techfield')
    technologies = techs if techs else ''
    fields = request.form.getlist('search_field')
    search_fields = fields if fields else None
    sortby = request.form.get('sort_field', 'start_date')
    sort_order = request.form.get('sort', 'desc')
        
    search_function = data.search(appdata, sort_order=sort_order, 
                                    sort_by=sortby, techniques=technologies, 
                                    search=sanitized_search,
                                    search_fields=search_fields)
    results_count = len(search_function)
    return render_template("search.html", data=search_function, 
                            count=results_count, term=sanitized_search, 
                            fields=fields, techs=techs, sort=sort_order, 
                            sortby=sortby, info=data.load("main.json"))
    
@app.errorhandler(404)
def page_not_found(error):
    """
    Returns a user friendly message if 
    the requested page was not found on the server.
    """
    return render_template('404.html'), 404
    
@app.errorhandler(400)
def bad_request(error):
    """
    Returns a user friendly message if a bad request occured.
    """
    return render_template('400.html'), 400
    
@app.errorhandler(500)
def other(error):
    """
    Returns a user friendly message if server error occured.
    """
    return render_template('error.html'), 500


if __name__ == "__main__":
    main()
