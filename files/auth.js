var PASSWORD = "";
var match = document.cookie.match(/grader_cred=[^;]+/);
if (match != null) {
  var array = decodeURIComponent(match[0].split("=")[1]).split(";");
  var username = array[0];
  tryAuth(array[0], array[1], false);
}
else{
  if(document.getElementsByTagName("title")[0].innerHTML != "Site under Maintenance"){
  admin_pass("a","");
  }
}
var mode = 0;
 
var running = ""
function admin_pass(username,password){
fetch("/running").then(function(response){return response.text()}).then(function(text){
  running = text=="True";
  var auth;
  fetch("/admin_auth", {
        method: "POST",
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: username,
          password: password,
        })
      }).then(function(response) {
        return response.text();
      }).then(function(text) {
        if (text != "auth") {
          if(document.getElementsByTagName("TITLE")[0].innerHTML == "SUDO"){
            console.log("Hey, What are you doing here!")
            window.location.replace("/");
          }
          if(!running){
          console.log("Hey, you're not an admin!");
          window.location.replace("/maintenance");
          }
        }
        else{
          console.log("Welcome, Admin!");
        }
      })}
);
}

function updatepts() {
  var names = document.getElementsByClassName("name");
  if (!(document.getElementById("home_button").hidden)) {
    var user = document.getElementById("home_button").innerHTML.slice(18, -18);
    if (user !== "") {
      fetch("/scores/" + user).then(function(response) {
        return response.text();
      }).then(function(text) {
        if (text !== "") {
          var scores = JSON.parse(text);
          var pts = document.getElementsByClassName("pts");
          var names = document.getElementsByClassName("name");
          for (var index = 0; index < pts.length; index++) { 
            var id = names[index].href.split("/")[4];
            if (id in scores) {
              pts[index].innerHTML = scores[id] + "/" + pts[index].innerHTML.split("/")[1]
            } else {
              pts[index].innerHTML = "0" + "/" + pts[index].innerHTML.split("/")[1]

            }
          }
          pts = document.getElementsByClassName("featured_pts");
          names = document.getElementsByClassName("featured_name");
          for ( index = 0; index < pts.length; index++) { 
            var id = names[index].href.split("/")[4];
            if (id in scores) {
              pts[index].innerHTML = scores[id] + "/" + pts[index].innerHTML.split("/")[1]
            } else {
              pts[index].innerHTML = "0" + "/" + pts[index].innerHTML.split("/")[1]

            }
          }
          
        }
      });
    }
  }

}

function sign_in() {
  if (mode == 1) {
    document.getElementById("sign-in").hidden = true;
    mode = 0;
  } else {
    document.getElementById("sign-in").hidden = false;
    document.getElementById("repeated").hidden = true;
    mode = 1;
  }
}

function sign_up() {
  if (mode == 2) {
    document.getElementById("sign-in").hidden = true;
    mode = 0;
  } else {
    document.getElementById("sign-in").hidden = false;
    document.getElementById("repeated").hidden = false;
    mode = 2;
  }
}

function sign_out() {
  mode = 0;
  document.cookie = "grader_cred=;max-age=0;";
  location.reload();
}

function get_username() {
  return username;
}

function auth() {
  var username = document.getElementById("username").value.trim();
  var password = document.getElementById("password").value;
  var repeated = document.getElementById("repeated").value;
  if (username.match(/[A-Za-z0-9\-._ ]+/)[0] != username) {
    alert("Username may only contain letters, numbers, dashes, underscores, dots, and spaces.");
  } else if (mode === 0) {
    console.log("Auth function was called with no selected sign-in/-up mode!");
  } else if (mode == 1) {
    console.log("Signing in...");
    tryAuth(username, password, true);
  } else if (mode == 2) {
    if (password == repeated) {
      console.log("Signing up...");
      fetch("/reguser", {
        method: "POST",
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: username,
          password: hash(password),
        })
      }).then(function(response) {
        return response.text();
      }).then(function(text) {
        if (text == "auth") {
          successAuth(username, password, true);
        } else if (text == "userexists") {
          console.log("User exists!");
          alert("This username is already in use!");
        }
      });
    } else {
      console.log("Password mismatch!");
      alert("Passwords do not match!");
    }
  }
}

function tryAuth(username, password, dohash) {
  admin_pass(username,dohash ? hash(password) : password); 
  fetch("/authuser", {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      username: username,
      password: dohash ? hash(password) : password
    })
  }).then(function(response) {
    return response.text();
  }).then(function(text) {
    if (text == "auth") {
      successAuth(username, password, dohash);
    }

  });
}

function successAuth(username, password, write_cookie) {
  console.log("Authenticated!");
  document.getElementById("home_button").innerHTML = "&nbsp;&nbsp;&nbsp;" + username + "&nbsp;&nbsp;&nbsp;";
  if (write_cookie) document.cookie = "grader_cred=" + encodeURIComponent(username + ";" + hash(password) + ";path=/");
  PASSWORD = write_cookie ? hash(password) : password;
  document.getElementById("username").value = "";
  document.getElementById("password").value = "";
  document.getElementById("repeated").value = "";
  document.getElementById("auth_bar").hidden = true;
  document.getElementById("user_bar").hidden = false;
  document.getElementById("sign-in").hidden = true;
  var elements = document.getElementsByClassName("enable");
  for (var x = 0; x < elements.length; x++) {
    elements[x].disabled = false;
  }
  updatepts();
}

function hash(string) {
  var obj = new jsSHA("SHA-256", "TEXT");
  obj.update(string);
  return obj.getHash("HEX");
}