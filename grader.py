import os, sys, threading, json, shutil, base64, requests, io, traceback, html

from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from threading import Thread
from subprocess import *

from time import time
import subprocess

users = {}

running = True

def grade(command, tests, cwd):
    for suite_num, (points, i_suite, o_suite) in enumerate(zip(tests["points"], tests["inputs"], tests["outputs"])):
        yield (0, suite_num, points)
        skip = False
        for test_num, (i, o) in enumerate(zip(i_suite, o_suite)):
            if skip:
                yield (5, test_num)
            else:
                start = time()
                try:
                    i, o = open(i, "r"), open(o, "r")
                    expected = o.read().strip()
                    actual = "".join(map(chr, check_output(command, cwd = cwd, stdin = i, stderr = sys.stdout, timeout = tests["timelimit"]))).strip()
                    if expected == actual:
                        yield (1, test_num, time() - start)
                    else:
                        yield (2, test_num, time() - start, expected, actual); skip = True
                except subprocess.TimeoutExpired:
                    yield (3, test_num, time() - start); skip = True
                except:
                    traceback.print_exc()
                    yield (4, test_num, time() - start); skip = True
        yield (6, (1 - skip) * points)
    yield (7,)

def flatten(gen):
    while True:
        yield from next(gen)

def test(command, tests, cwd, output = print, user = None, index = 0, length = 0, debug = False):
    grader = flatten(grade(command, tests, cwd))
    total = 0
    while True:
        num = next(grader)
        if num == 0:
            output("Test Suite %d [%d points]" % (next(grader) + 1, next(grader)))
            while True:
                id = next(grader)
                if id == 1: output("Test %d passed: %s seconds" % (next(grader) + 1, round(next(grader), 2)))
                if id == 2: output("Test %d failed: Wrong Answer: %s seconds%s" % (next(grader) + 1, round(next(grader), 2), ["", ": expected %r, got %r" % (next(grader), next(grader))][debug]))
                if id == 3: output("Test %d failed: Time Limit Exceeded: %s seconds" % (next(grader) + 1, round(next(grader), 2)))
                if id == 4: output("Test %d failed: Runtime Error: %s seconds" % (next(grader) + 1, round(next(grader), 2)))
                if id == 5: output("Test %d skipped" % (next(grader) + 1))
                if id == 6: total += next(grader); break
        if num == 7:
            break
    if user:
        if user not in users:
            users[user] = [0] * length
        users[user][index] = max(users[user][index], total)
    output("Total Points: %d / %d" % (total, sum(tests["points"])))

def do_tests(array, command, tests):
    def function():
        gen = grade(command, tests)
        while True:
            try:
                array.append(next(gen))
            except StopIteration:
                break
    return function

name_to_command = {
    "Python 3.6.4": ["python3.6 Main.py"],
    "Python 2.7.6": ["python2 Main.py"],
    "Java 9.0.4": ["javac Main.java", "java Main"],
    "C++ (g++) 4.8.4": ["g++ Main.cpp -o a.out", "./a.out"],
    "Ruby 2.5.0": ["bash /home/cabox/workspace/contest-grader/ruby.sh"],
    "Ruby 1.9.3p484": ["ruby Main.rb"],
    "Haskell (GHC 7.6.3)": ["ghc -o Main Main.hs", "./Main"],
    "COBOL (OpenCOBOL 1.1.0)": ["cobc -free -x -o Main Main.cbl", "./Main"],
    "Kotlin 1.2.30 (SUPER SLOW)": ["/home/cabox/workspace/contest-grader/kotlinc/bin/kotlinc Main.kt -include-runtime -d Main.jar", "java -jar Main.jar"]
}

file_exts = {
    "Python 3.6.4": ".py",
    "Python 2.7.6": ".py",
    "Java 9.0.4": ".java",
    "C++ 4.8.4": ".cpp",
    "Ruby 2.5.0": ".rb",
    "Ruby 1.9.3p484": ".rb",
    "Haskell (GHC 7.6.3)": ".hs",
    "COBOL (OpenCOBOL 1.1.0)": ".cbl",
    "Kotlin 1.2.30 (SUPER SLOW)": ".kt"
}

def get_data(name):
    return json.loads(requests.get(prefix + "data/" + name).text)

def get_problem_filename(problem):
    return "p{num}grader".format(num = 1 + getProblems().index(problem + ".html"))

submissions = {}

def process_submission(username, code, language, problem):
    submission = (username, language, problem, [])
    id = int(time() * 1000)
    submissions[id] = submission
    problems = getProblems()
    def proc():
        commands = name_to_command[language]
        grader = get_problem_filename(problem)
        foldername = "Submission%d" % id
        try:
            shutil.rmtree(foldername)
        except:
            pass
        os.mkdir(foldername)
        filename = foldername + "/Main" + file_exts[language]
        filename_no_ext = "".join(filename.split(".")[:-1])
        with open(filename, "w+") as f:
            f.write(code)
        for command in commands[:-1]:
            call(command.split(), cwd = foldername)
        test(commands[-1].split(), get_data(grader), foldername, submission[3].append, username, problems.index(problem + ".html"), len(problems))
        shutil.rmtree(foldername)
    threading.Thread(target = proc).start()
    return "/submission/%d" % id

def get_sorted_users():
    return sorted(list(users), key = lambda u: sum(users[u]), reverse = True)

prefix = "http://127.0.0.1:6000/"

def getProblems():
    return json.loads(requests.get(prefix + "problems").text)

def getFullNames():
    return json.loads(requests.get(prefix + "fullnames").text)

@app.route("/")
def serveRoot():
    if not running: return "<h2>Contest is currently paused...</h2>"
    with open("static/index.html", "r") as f:
        return f.read() % (("<br />".join("<a href='/problem/%d'>%s</a>" % (i, getFullNames()[i]) for i in range(len(getProblems())))) or "There are currently no problems.")

@app.route("/sudo")
def sudo():
    with open("static/sudo.html", "r") as f:
        return f.read()

@app.route("/js-sha")
def js_sha():
    with open("static/jsSHA-2.3.1/src/sha.js", "r") as f:
        return f.read()

@app.route("/clear_leaderboard/<userhash>")
def clear_leaderboard(userhash):
    global users
    if userhash == serverhash:
        users = {}
    return ""

@app.route("/kick_leaderboard/<username>/<userhash>")
def kick_leaderboard(username, userhash):
    global users
    if userhash == serverhash:
        user = "".join(map(chr, base64.b64decode(username.replace("-", "/"))))
        if user in users:
            del users[user]
    return ""

@app.route("/set_user_points/<username>/<points>/<userhash>")
def set_user_points(username, points, userhash):
    global users
    if userhash == serverhash:
        user = "".join(map(chr, base64.b64decode(username.replace("-", "/"))))
        users[user] = list(map(int, points.split("-")))
    return ""

@app.route("/stop_contest/<userhash>")
def stop_contest(userhash):
    global running
    if userhash == serverhash:
        running = False
    return ""

@app.route("/start_contest/<userhash>")
def start_contest(userhash):
    global running
    if userhash == serverhash:
        running = True
    return ""

@app.route("/set_contest/<contestname>/<userhash>")
def set_contest(contestname, userhash):
    if userhash == serverhash:
        requests.get(prefix + "set_contest/" + contestname + "/" + userhash)
    return ""

@app.route("/problem/<int:id>")
def problem(id):
    if not running: return "<h2>Contest is currently paused...</h2>"
    return requests.get(prefix + "problem/" + str(id)).text

@app.route("/leaderboard")
def leaderboard():
    return open("static/leaderboard.html", "r").read() % "".join(
        "<tr><td>%s</td><td>%d (%s)</td></tr>" % (html.escape(user), sum(users[user]), " / ".join(map(str, users[user]))) for user in get_sorted_users())

@app.route("/enter_submission")
def enter_submission():
    if not running: return "<h2>Contest is currently paused...</h2>"
    with open("static/template.html", "r") as f:
        return f.read() % (
            "".join(
                "<option value='{language}'>{language}</option>".format(language = language)
            for language in name_to_command.keys()),
            "".join(
                "<option value='{id}'>{problem}</option>".format(id = p[:-5], problem = getFullNames()[i])
            for i, p in enumerate(getProblems())))

@app.route("/submit/<data>")
def submit(data):
    if not running: return "/"
    return process_submission(**json.loads(base64.b64decode(data.replace(".", "/")).decode('utf-8')))

@app.route("/submission/<int:id>")
def submission(id):
    if id not in submissions:
        return "<p style='font-family:monospace'>Sorry, submission not found with that ID.</p>"
    return "<style>body{font-family: monospace;}</style><a href='/'>&lt;&lt;&lt; Back</a><br /><br /><a href='/enter_submission'>Resubmit</a><br /><br />Submitted by '%s' in %s for %s<br /><br />" % submissions[id][:3] + "<br />".join(submissions[id][3])

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except:
            port = 80
    else:
        port = 80
    if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
        serverhash = sys.argv[2]
    else:
        serverhash = "7d509328bd69ef7406baf28bd9897c0bf724d8d716b014d0f95f2e8dd9c43a06"
    app.run(host = "0.0.0.0", port = port, debug = "--debug" in sys.argv)
