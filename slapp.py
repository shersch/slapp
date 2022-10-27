import rumps
import requests
import json
import time
from pathlib import Path
import os
import sys

rumps.debug_mode(True)

home = str(Path.home())
slappdir = Path(home + "/.slapp")
conf = Path(home + "/.slapp/config.json")

# check for config directory
if slappdir.is_dir():
    pass
else:
    os.makedirs(slappdir)

# check for config file
if conf.is_file():
    pass
else:
    # create config file
    f = open("sample.txt")
    with open(conf, "w") as c:
        c.write(f.read())
    c.close()
    f.close()
    window = rumps.Window()
    window.title = 'Slapp Configurator'
    window.message = 'Please enter your first name:'
    name = window.run()
    window.message = 'Please enter your api key:'
    key = window.run()

    # prompt user for first name and API key
    with open(home + "/.slapp/config.json","r+") as cfile:
        data = json.load(cfile)
        data["user"]['firstName'] = name.text
        data["user"]["apiKey"] = key.text
        cfile.seek(0)
        json.dump(data, cfile)
        cfile.truncate()

# load config
with open(home + "/.slapp/config.json") as jsonfile:
	data = json.load(jsonfile)

firstName = data["user"]["firstName"]
apiKey = data["user"]["apiKey"]
headers = {
    "name": firstName,
    "pretty": "1",
    "Authorization": "Bearer " + apiKey,
    "Content-Type": "application/json"
    }
get = "https://slack.com/api/users.profile.get"
set = "https://slack.com/api/users.profile.set"
pause_notifications = "https://slack.com/api/dnd.setSnooze"
resume_notifications = "https://slack.com/api/dnd.endSnooze"
away = "https://slack.com/api/users.setPresence"

configObjects = ["Current Status", "Clear Status"]
for item in data["menu"]:
    configObjects.append(item["name"])
configObjects.append("Update")

def userclick(app, menuitem):
    for item in data["menu"]:
        if item["name"] == menuitem.title:
            for p in item["parameters"]:
                if p == "do_not_disturb":
            #if item["parameters"]["do_not_disturb"] in item["parameters"]:
                    if item["parameters"]["do_not_disturb"] == True:
                        snooze_time = float(item["parameters"]["status_expiration"]) * 60
                        requests.post(pause_notifications, headers={
                            "pretty": "1",
                            "Authorization": "Bearer " + apiKey
                            }, params={"num_minutes": snooze_time})
                if p == "away":
                # if item["parameters"]["away"] in item["parameters"]:
                    if item["parameters"]["away"] == True:
                        requests.post(away, headers={
                            "pretty": "1",
                            "Authorization": "Bearer " + apiKey
                            }, params={"presence": "away"})

            exp_time = float(item["parameters"]["status_expiration"]) * 3600 + time.time()
            payload = {
                "profile": {
                    "status_text": item["parameters"]["status_text"],
                    "status_emoji": item["parameters"]["status_emoji"],
                    "status_expiration": exp_time
                }
            }
            requests.post(set, headers=headers, json=payload)
            rumps.notification("Slapp", "Slack status update", menuitem.title)

class Slapp(rumps.App):

    for object in configObjects:
        userclick = rumps.clicked(object)(userclick)

    def __init__(self):
        super(Slapp, self).__init__("Slapp")
        self.menu = configObjects

@rumps.clicked("Current Status")
def get_status(self):
    status = requests.get(get, headers=headers)
    rumps.notification("Slapp", "Slack current status", status.json()["profile"]["status_text"] + "\n" + status.json()["profile"]["status_emoji"])

@rumps.clicked("Clear Status")
def clear_status(self):
    payload = {"profile": {"status_text": "", "status_emoji": "", "status_expiration": int(time.time()) + 1 }}
    requests.post(set, headers=headers, json=payload)
    requests.post(resume_notifications, headers={"pretty": "1","Authorization": "Bearer " + apiKey})
    requests.post(away, headers={"pretty": "1", "Authorization": "Bearer " + apiKey}, params={"presence": "auto"})
    rumps.notification("Slapp", "Slack status update", "Status cleared")

@rumps.clicked('Update')
def restart(self):
    os.execl(sys.executable, sys.executable, * sys.argv)

if __name__ == "__main__":
    Slapp().run()