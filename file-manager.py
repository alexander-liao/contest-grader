from flask import Flask
from flask_cors import CORS

import json, sys, os, base64

app = Flask(__name__)
CORS(app)

@app.route("/set_contest/<contestname>/<userhash>")
def set_contest(contestname, userhash):
    print(base64.b64decode(contestname.replace("-", "/")))
    if userhash == serverhash:
        with open("static/contest.txt", "w") as f:
            f.write("".join(map(chr, base64.b64decode(contestname.replace("-", "/")))))
    return ""

@app.route("/current-contest")
def getCurrentContest():
    with open("static/contest.txt", "r") as f:
        return f.read().strip()

def contestIsOngoing():
    return getCurrentContest() != ""

@app.route("/problems")
def serveProblems():
    return json.dumps(getProblems())

def getProblems():
    try:
        return sorted(os.listdir("static/contests/%s/files" % getCurrentContest()))
    except:
        return []

@app.route("/problem/<int:id>")
def problem(id):
    with open("static/contests/%s/files/" % getCurrentContest() + getProblems()[id], "r") as f:
        return f.read()

def fullname(filename):
    with open("static/contests/%s/files/" % getCurrentContest() + filename, "r") as f:
        return f.read().split("\n")[0][5:-4]

@app.route("/fullnames")
def getFullNames():
    return json.dumps(list(map(fullname, getProblems())))

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
    if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
        serverhash = sys.argv[2]
    else:
        serverhash = "7d509328bd69ef7406baf28bd9897c0bf724d8d716b014d0f95f2e8dd9c43a06"
    app.run(host = "0.0.0.0", port = port)
