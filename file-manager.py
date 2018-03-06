from flask import Flask
from flask_cors import CORS

import json, sys, os

app = Flask(__name__)
CORS(app)

@app.route("/current-contest")
def getCurrentContest():
    with open("static/contest.txt", "r") as f:
        return f.read().strip()

def contestIsOngoing():
    return getCurrentContest() != ""

@app.route("/problems")
def getProblems():
    return json.dumps(sorted(os.listdir("static/contests/%s/files" % getCurrentContest())))

def fullname(filename):
    with open("static/contests/%s/files/" % getCurrentContest() + filename, "r") as f:
        return f.read().split("\n")[0][5:-4]

@app.route("/fullnames")
def getFullNames():
    return json.dumps(list(map(fullname, json.loads(getProblems()))))

@app.route("/data/<name>")
def getData(name):
    contest = getCurrentContest()
    data = getattr(getattr(__import__("static.contests.%s.Data.%s" % (contest, name)).contests, contest).Data, name)
    return json.dumps({
        "inputs": data.inputs,
        "outputs": data.outputs,
        "timelimit": data.timelimit,
        "points": data.points
    })

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except:
            port = 6000
    else:
        port = 6000
    app.run(host = "0.0.0.0", port = port)
