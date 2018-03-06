import os, sys, threading, json, shutil, base64, requests, io

from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from threading import Thread
from subprocess import *

from time import time

users = {}

def grade(command, tests, cwd):
    for suite_num, (points, i_suite, o_suite) in enumerate(zip(tests["points"], tests["inputs"], tests["outputs"])):
        yield (0, suite_num, points)
        skip = False
        for test_num, (i, o) in enumerate(zip(i_suite, o_suite)):
            if skip:
                yield (5, test_num)
            else:
                try:
                    i, o = open(i, "r"), open(o, "r")
                    start = time()
                    expected = o.read().strip()
                    actual = "".join(map(chr, check_output(command, cwd = cwd, stdin = i, stderr = sys.stdout, timeout = tests["timelimit"]))).strip()
                    if expected == actual:
                        yield (1, test_num, time() - start)
                    else:
                        yield (2, test_num, time() - start, expected, actual); skip = True
                except TimeoutExpired:
                    yield (3, test_num, time() - start); skip = True
                except:
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
    "Python 3.6.2": ["python3 Main.py"],
    "Python 2.7.13": ["python2 Main.py"],
    "Java 1.8.0_161": ["javac Main.java", "java Main"],
    "C++ 7.2.1": ["g++ Main.cpp -o a.out", "./a.out"],
    "Ruby 2.4.3": ["ruby Main.rb"],
}

file_exts = {
    "Python 3.6.2": ".py",
    "Python 2.7.13": ".py",
    "Java 1.8.0_161": ".java",
    "C++ 7.2.1": ".cpp",
    "Ruby 2.4.3": ".rb"
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
    return sorted(list(users), key = lambda u: sum(users[u]))

prefix = "http://e6b3c859.ngrok.io/"

def getProblems():
    return json.loads(requests.get(prefix + "problems").text)

def getFullNames():
    return json.loads(requests.get(prefix + "fullnames").text)

@app.route("/")
def serveRoot():
    with open("static/index.html", "r") as f:
        return f.read() % (("<br />".join("<a href='/problem/%d'>%s</a>" % (i, getFullNames()[i]) for i in range(len(getProblems())))) or "There are currently no problems.")

@app.route("/problem/<int:id>")
def problem(id):
    with open("static/problems/%s" % getProblems()[id], "r") as f:
        return f.read()

@app.route("/leaderboard")
def leaderboard():
    return open("static/leaderboard.html", "r").read() % "".join(
        "<tr><td>%s</td><td>%d (%s)</td></tr>" % (user, sum(users[user]), " / ".join(map(str, users[user]))) for user in get_sorted_users())

@app.route("/enter_submission")
def enter_submission():
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
    return process_submission(**json.loads(base64.b64decode(data.replace(".", "/"))))

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
    app.run(host = "0.0.0.0", port = port)
