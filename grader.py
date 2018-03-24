import os, sys, threading, json, shutil, base64, requests, io, traceback, html, shlex

from flask import Flask, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from threading import Thread
from subprocess import *

from time import time
import subprocess

import logging
\
debug = "--debug" in sys.argv

if not debug: logging.getLogger("werkzeug").setLevel(logging.ERROR)

users = json.load(open("files/leaderboard.json"))

running = eval(open("files/running.txt", "r").read().strip())

def grade(command, tests, cwd):
  for suite_num, subtask in enumerate(tests):
    points = subtask["points"]
    tasks = subtask["tests"]
    timelimit = subtask["timelimit"]
    yield (0, suite_num, points)
    skip = False
    for test_num, (i, o) in enumerate(tasks):
      if skip:
        yield (5, test_num)
      else:
        start = time()
        try:
          expected = o.strip()
          actual = "".join(map(chr, check_output(command, cwd = cwd, input = bytes(i, "utf8"), stderr = sys.stdout, timeout = timelimit))).strip()
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

def test(command, tests, cwd, output = print, user = None, problem = ""):
  debug = "--debug" in sys.argv
  grader = flatten(grade(command, tests, cwd))
  total = 0
  while True:
    num = next(grader)
    if num == 0:
      suite = next(grader) + 1
      points = next(grader)
      output("Test Suite %d [%d point%s]" % (suite, points, "s" * (points != 1)))
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
      users[user] = {"scores": {}, "recency": time()}
    if total > users[user]["scores"].get(problem, 0):
      users[user]["scores"][problem] = total
      users[user]["recency"] = time()
    update_users()
  output("Total Points: %d / %d" % (total, sum(subtask["points"] for subtask in tests)))

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
  "C++ (g++) 4.8.4": ".cpp",
  "Ruby 2.5.0": ".rb",
  "Ruby 1.9.3p484": ".rb",
  "Haskell (GHC 7.6.3)": ".hs",
  "COBOL (OpenCOBOL 1.1.0)": ".cbl",
  "Kotlin 1.2.30 (SUPER SLOW)": ".kt"
}

def get_data(name):
  with open("files/problems/%s/tests.json" % name, "r", encoding = "utf-8") as f:
    return json.load(f)

def update_users():
  with open("files/leaderboard.json", "w") as f:
    f.write(json.dumps(users, indent = 4))

submissions = {}

def process_submission(username, code, language, problem):
  username = username.strip()
  if len(username) > 24 or len(username) == 0:
    return "/urbad"
  submission = (username, language, problem, [])
  id = int(time() * 1000)
  submissions[id] = submission
  problems = getProblems()
  def proc():
    commands = name_to_command[language]
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
      call(shlex.split(command), cwd = foldername)
    test(shlex.split(commands[-1]), get_data(problem), foldername, submission[3].append, username, problem)
    shutil.rmtree(foldername)
  threading.Thread(target = proc).start()
  print("{username} created a submission in {language} for {problem} with id {id}".format(username = username, language = language, problem = problem, id = id))
  print("=" * 50)
  print(code)
  print("=" * 50)
  return "/submission/%d" % id

def get_sorted_users():
  return sorted(list(users), key = lambda u: (sum(users[u]["scores"][p] for p in users[u]["scores"] if p in getProblems()), -users[u]["recency"]), reverse = True)

def getProblems():
  with open("files/contest.txt", "r") as f:
    return f.read().splitlines()

def fullname(name):
  with open("files/problems/%s/problem.json" % name, "r", encoding = "utf8") as f:
    return json.loads(f.read())["title"]

def getFullNames():
  return list(map(fullname, getProblems()))

def decode(string):
  return base64.b64decode(string.replace("-", "/")).decode("utf-8")

@app.route("/")
def serveRoot():
  if not running: return "<link rel='stylesheet' href='/stylesheet.css' type='text/css' /><h2>Contest is currently paused...</h2>"
  l = max(map(len, getFullNames()))
  with open("files/index.html", "r") as f:
    return f.read() % (
      ("<br /><br />".join(
         "<a class='buttonlink' href='/problem/%d'>%s</a> %s" % (
           i,
           getFullNames()[i] + "&nbsp;" * (l - len(getFullNames()[i])),
           ", ".join(json.load(open("files/problems/%s/problem.json" % e))["tags"]))
         for i, e in enumerate(getProblems()))
      ) or "There are currently no problems.")

@app.route("/tagged/<tagname>")
def serveTagged(tagname):
  if not running: return "<link rel='stylesheet' href='/stylesheet.css' type='text/css' /><h2>Contest is currently paused...</h2>"
  return ""

@app.route("/stylesheet.css")
def serveStyleSheet():
  with open("files/stylesheet.css", "r") as f:
    return Response(f.read(), mimetype="text/css")

@app.route("/favicon.ico")
def serveIcon():
  with open("files/favicon.ico", "rb") as f:
    return Response(f.read(), mimetype="image/x-icon")

@app.route("/sudo")
def sudo():
  if debug: print("User accessed SUDO page!")
  with open("files/sudo.html", "r") as f:
    return f.read()

@app.route("/urbad")
def urbad():
  return "<link rel='stylesheet' href='/stylesheet.css' type='text/css' /><code><a class='buttonlink' href='/'>&lt;&lt;&lt; Back</a>&nbsp;&nbsp;<a class='buttonlink' href='/enter_submission'>Submit &gt;&gt;&gt;</a></code><h1>Username cannot exceed 24 characters or be blank</h1>"

@app.route("/js-sha")
def js_sha():
  with open("files/jsSHA-2.3.1/src/sha.js", "r") as f:
    return f.read()

@app.route("/clear_leaderboard/<userhash>")
def clear_leaderboard(userhash):
  global users
  if userhash == serverhash:
    users = {}
    update_users()
    print("Leaderboard cleared!")
  else:
    if debug: print("Invalid password for clearing leaderboard!")
  return ""

@app.route("/kick_leaderboard/<username>/<userhash>")
def kick_leaderboard(username, userhash):
  if userhash == serverhash:
    __kick_leaderboard(decode(username).strip())
  else:
    if debug: print("Invalid password for kicking user!")
  return ""

def __kick_leaderboard(username):
  if username in users:
    del users[username]
    update_users()
    print("Kicked {username} from the leaderboard!".format(username = username))
  else:
    print("Could not kick {username} from the leaderboard because the user does not exist!".format(username = username))

@app.route("/set_user_points/<username>/<points>/<userhash>")
def set_user_points(username, points, userhash):
  if userhash == serverhash:
    __set_points(decode(username).strip(), list(map(int, points.split("-"))))
  else:
    if debug: print("Invalid password for setting user points!")
  return ""

def __set_points(username, points):
  if username not in users:
    users[username] = {"scores": {}, "recency": time()}
  users[username]["recency"] = time()
  for problem_name, point in zip(getProblems(), points):
    users[username]["scores"][problem_name] = point
  print("Set {username}'s points to {points}".format(username = username, points = points))

@app.route("/stop_contest/<userhash>")
def stop_contest(userhash):
  global running
  if userhash == serverhash:
    running = False
    with open("files/running.txt", "w") as f:
      f.write("False")
    print("Contest stopped!")
  else:
    if debug: print("Invalid password for stopping contest!")
  return ""

@app.route("/start_contest/<userhash>")
def start_contest(userhash):
  global running
  if userhash == serverhash:
    running = True
    with open("files/running.txt", "w") as f:
      f.write("True")
    print("Contest started!")
  else:
    if debug: print("Invalid password for starting contest!")
  return ""

@app.route("/add_problem/<problem_name>/<userhash>")
def add_problem(problem_name, userhash):
  if userhash == serverhash:
    __add_problem(decode(problem_name).strip())
  else:
    if debug: print("Invalid password for adding problem!")
  return ""

def __add_problem(name):
  if name in os.listdir("files/problems"):
    with open("files/contest.txt", "a", encoding = "utf-8") as f:
      f.write(name + "\n")
    print("Added {name} to the contest!".format(name = name))
  else:
    print("Could not add {name} to the contest because the problem does not exist!".format(name = name))

@app.route("/rm_problem/<problem_name>/<userhash>")
def rm_problem(problem_name, userhash):
  if userhash == serverhash:
    __rm_problem(decode(problem_name).strip())
  else:
    if debug: print("Invalid password for removing problem!")
  return ""

def __rm_problem(name):
  with open("files/contest.txt", "r", encoding = "utf-8") as f:
    lines = f.read().splitlines()
  index = lines.index(name) if name in lines else -1
  if index != -1:
    print("Removed {name} from the contest!".format(name = name))
  else:
    print("Could not remove {name} from the contest because the problem was not in the contest!".format(name = name))
  with open("files/contest.txt", "w", encoding = "utf-8") as f:
    f.write("\n".join(line for line in lines if line != name) + "\n")

@app.route("/reset_contest/<userhash>")
def reset_contest(userhash):
  if userhash == serverhash:
    __reset_contest()
    print("Contest reset!")
  else:
    if debug: print("Invalid password for resetting the contest!")
  return ""

def __reset_contest():
  with open("files/contest.txt", "w", encoding = "utf-8") as f:
    f.write("")

@app.route("/set_contest/<contest>/<userhash>")
def set_contest(contest, userhash):
  if userhash == serverhash:
    __set_contest(decode(contest))
  else:
    if debug: print("Invalid password for setting the contest!")
  return ""

def __set_contest(contest):
  if contest + ".config" in os.listdir("files/contests"):
    with open("files/contests/" + contest + ".config", "r", encoding = "utf-8") as f:
      with open("files/contest.txt", "w", encoding = "utf-8") as g:
        g.write(f.read())
    print("Set the contest to " + contest + "!")
  else:
    print("Could not find contest " + contest + "!")

@app.route("/load_problem/<problem>/<userhash>")
def load_problem(problem, userhash):
  if userhash == serverhash:
    return __load_problem(decode(problem))
  else:
    if debug: print("Invalid password for loading a problem!")
  return ""

def __load_problem(problem):
  if problem in os.listdir("files/problems"):
    print("Loaded problem " + problem + "!")
    with open("files/problems/%s/problem.json" % problem, "r") as f:
      return f.read()
  else:
    print("Could not find problem " + problem + "!")
    return ""

@app.route("/load_config/<contest>/<userhash>")
def load_config(contest, userhash):
  if userhash == serverhash:
    return __load_config(decode(contest))
  else:
    if debug: print("Invalid password for loading a contest configuration!")
  return ""

def __load_config(contest):
  if contest + ".config" in os.listdir("files/contests"):
    print("Loaded configuration for contest " + contest + "!")
    with open("files/contests/" + contest + ".config", "r", encoding = "utf-8") as f:
      return f.read().strip()
  else:
    print("Could not find contest " + contest + "!")
    return ""

@app.route("/save_config/<contest>/<config>/<userhash>")
def save_config(contest, config, userhash):
  if userhash == serverhash:
    __save_config(decode(contest), decode(config))
  else:
    if debug: print("Invalid password for setting a contest configuration!")
  return ""

def __save_config(contest, config):
  with open("files/contests/" + contest + ".config", "w", encoding = "utf-8") as f:
    f.write(config.strip() + "\n")
  print("Set configuration for contest " + contest + "!")

@app.route("/del_problem/<problem_name>/<userhash>")
def del_problem(problem_name, userhash):
  if userhash == serverhash:
    __del_problem(decode(problem_name).strip())
  else:
    if debug: print("Invalid password for deleting a problem!")
  return ""

def __del_problem(name):
  shutil.rmtree("files/problems/" + name)
  print("Deleted {name} permanently!".format(name = name))
  __rm_problem(name)

@app.route("/write_problem/<content>/<userhash>")
def write_problem(content, userhash):
  if userhash == serverhash:
    problem = json.loads(decode(content))
    problem["tags"] = list(map(str.strip, problem["tags"].split(",")))
    print("[-- writing problem {problem_id} --]".format(problem_id = problem["id"]))
    if problem["id"] not in os.listdir("files/problems"):
      print("* creating problem folder...")
      os.mkdir("files/problems/" + problem["id"])
    with open("files/problem_format.html", "r", encoding = "utf-8") as f:
      smpl = problem["smpl"].split("\n")
      smpl = [(smpl[i * 2], smpl[i * 2 + 1]) for i in range(len(smpl) // 2)]
      print("* writing problem JSON file...")
      with open("files/problems/%s/problem.json" % problem["id"], "w") as f:
        f.write(json.dumps(problem, indent = 4))
    print("* done!")
  else:
    if debug: print("Invalid password for writing a problem!")
  return ""
    

@app.route("/create_problem/<content>/<userhash>")
def create_problem(content, userhash):
  try:
    if userhash == serverhash:
      problem = json.loads(decode(content))
      print("[-- creating problem {problem_id} --]".format(problem_id = problem["id"]))
      write_problem(content, userhash)
      print("=" * 50)
      print(problem["impl"])
      print("=" * 50)
      print(problem["genr"])
      print("=" * 50)
      os.chdir("files/problems/" + problem["id"])
      with open(problem["impl_filename"], "w") as f:
        f.write(problem["impl"])
      with open(problem["genr_filename"], "w") as f:
        f.write(problem["genr"])
      print("* running pre-commands...")
      os.system(problem["impl_precommand"])
      os.system(problem["genr_precommand"])
      pts = list(map(int, problem["pts"].split("/")))
      tls = list(map(int, problem["tls"].split("/"))) * (len(pts) if "/" not in problem["tls"] else 1)
      tcc = list(map(int, problem["tcc"].split("/"))) * (len(pts) if "/" not in problem["tcc"] else 1)
      tests = []
      impl_command, genr_command = shlex.split(problem["impl_command"]), shlex.split(problem["genr_command"])
      for suiteno, (pt, tl, tc) in enumerate(zip(pts, tls, tcc)):
        print("* generating suite {suiteno} of {total}...".format(suiteno = suiteno + 1, total = len(pts)))
        attrs = {}
        tests.append(attrs)
        attrs["timelimit"] = tl
        attrs["points"] = pt
        test_cases = []
        attrs["tests"] = test_cases
        for case in range(tc):
          test_in = check_output(genr_command, input = bytes(str(suiteno) + "\n" + str(case), "utf-8"))
          test_out = check_output(impl_command, input = test_in)
          test_cases.append((test_in.decode("utf-8"), test_out.decode("utf-8")))
      print("* writing test case JSON file...")
      with open("tests.json", "w") as f:
        f.write(json.dumps(tests, indent = 4))
      print("* running post-commands...")
      os.system(problem["impl_postcommand"])
      os.system(problem["genr_postcommand"])
      print("* cleaning up generation files...")
      os.remove(problem["impl_filename"])
      os.remove(problem["genr_filename"])
      os.chdir("../../..")
      print("* done!")
    else:
      if debug: print("Invalid password for creating a problem!")
  except:
    traceback.print_exc()
    os.chdir("/home/cabox/workspace/contest-grader")
  return ""

@app.route("/problem/<int:id>")
def problem(id):
  if not running: return "<h2>Contest is currently paused...</h2>"
  with open("files/problems/%s/problem.json" % getProblems()[id], "r") as p:
    with open("files/problem_format.html", "r") as f:
      p = json.loads(p.read())
      title = p["title"]
      desc = p["desc"]
      subt = p["subt"]
      inpt = p["inpt"]
      outp = p["outp"]
      smpl = p["smpl"].split("\n")
      return f.read() % (title, title, title, desc.replace("\n", "<br />"), inpt.replace("\n", "<br />"), outp.replace("\n", "<br />"), subt.replace("\n", "<br />"), "\n".join("<h3>Sample Input</h3>\n<table class='sample'><tr><td><code>%s</code></td></tr></table>\n<h3>Sample Output</h3>\n<table class='sample'><tr><td><code>%s</code></td></tr></table>" % (smpl[2*r], smpl[2*r+1]) for r in range(len(smpl)//2)))

@app.route("/leaderboard")
def leaderboard():
  problems = getProblems()
  config = [(user, [users[user]["scores"].get(problem, 0) for problem in problems]) for user in get_sorted_users()]
  return open("files/leaderboard.html", "r").read() % "".join(
    "<tr><td>%s</td><td>%d (%s)</td></tr>" % (html.escape(user), sum(cfg), " / ".join(map(str, cfg))) for user, cfg in config)

@app.route("/enter_submission")
def enter_submission():
  if not running: return "<h2>Contest is currently paused...</h2>"
  return sudo_enter_submission(serverhash, False)
  
@app.route("/sudo_enter_submission/<userhash>")
def sudo_enter_submission(userhash, sudomode = True):
  if userhash == serverhash:
    with open("files/template.html", "r") as f:
      return f.read() % (
        "".join(
          "<option value='{language}'>{language}</option>".format(language = language)
        for language in name_to_command.keys()),
        "".join(
          "<option value='{id}'>{problem}</option>".format(id = p, problem = getFullNames()[i])
        for i, p in enumerate(getProblems())),
      "submit_sudo/" + userhash if sudomode else "submit")
  else:
    return "<link rel='stylesheet' href='/stylesheet.css' type='text/css' /><a class='buttonlink' href='/'>what are you doing here</a>"

@app.route("/submit/<data>")
def submit(data):
  if not running: return "/"
  return process_submission(**json.loads(decode(data)))

@app.route("/submit_sudo/<userhash>/<data>")
def submit_sudo(userhash, data):
  return process_submission(**json.loads(decode(data)))

@app.route("/submission/<int:id>")
def submission(id):
  if id not in submissions:
    return "<link rel='stylesheet' href='/stylesheet.css' type='text/css' /><p style='font-family:monospace'>Sorry, submission not found with that ID.</p>"
  return "<link rel='stylesheet' href='/stylesheet.css' type='text/css' /><a class='buttonlink' href='/'>&lt;&lt;&lt; Back</a><br /><br /><a class='buttonlink' href='/enter_submission'>Resubmit</a><br /><br />Submitted by '%s' in %s for %s<br /><br />" % submissions[id][:3] + "<br />".join(submissions[id][3])

@app.route("/run_command/<command>/<userhash>")
def run_command(command, userhash):
  if userhash == serverhash:
    print("Processing manual command `{command}`".format(command = decode(command)))
    process_command(shlex.split(decode(command)))
  else:
    if debug: print("Invalid password for running command!")
  return ""

def process_command(command):
  if command == []:
    return
  if command[0] == "remove":
    __rm_problem(command[1])
  elif command[0] == "add":
    __add_problem(command[1])
  elif command[0] == "stop" or command[0] == "pause":
    stop_contest(serverhash)
  elif command[0] == "start" or command[0] == "resume":
    start_contest(serverhash)
  elif command[0] == "kick":
    __kick_leaderboard(command[1])
  elif command[0] == "clearboard":
    clear_leaderboard(serverhash)
  elif command[0] == "setpoints":
    __set_points(command[1], list(map(int, command[2].split("/"))))
  elif command[0] == "clear":
    sys.stdout.write("\033[2J\033[1;1H")
  elif command[0] == "eval":
    try:
      print(eval(command[1]))
    except:
      traceback.print_exc()
  elif command[0] == "shutdown":
    print("Server shutting down!")
    shutdown = request.environ.get("werkzeug.server.shutdown")
    if shutdown is not None:
      shutdown()
  else:
    threading.Thread(target = lambda: [call(command)] and os.chdir("/home/cabox/workspace/contest-grader")).start()

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
