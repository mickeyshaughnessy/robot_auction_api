# This example is for how to run a robot that connects to
# the robot services exchange /grab_job API endpoint.
import json, time, requests, hashlib
import config
from llm import generate_completion

job_prompt = """
You are the central control model for the robot.
Your current state is %s.

If job is null return GRAB_JOB to, you know, grab a new job.

return:
"""

class Robot():
    def __init__(self):
        self.RSE_url = "https://rse-api.com:5002/grab_job"
        self.state = {
            "job" : None,
            "location" : (0,0,0),
            "capabilities" : ["taxi", "delivery"]
            }
        self.seat = config.test_rsx2

    def get_RSE_body(self):
        return {
            "capabilities" : self.state['capabilities'],
            "lat" : self.state['location'][0],
            "lon" : self.state['location'][1],
            "max_distance" : 10, # change later
            "seat" : {
                "id" : self.seat.get("id"),
                "owner" : self.seat.get("owner"),
                "secret" : hashlib.md5(self.seat.get("phrase").encode()).hexdigest()
            }
        }

    def work(self):
        pass
        # Here do the robot working with a lower-level controller 

if __name__ == "__main__":
    robot = Robot() 
    while True:
        print(job_prompt % json.dumps(robot.state))
        _next = generate_completion(job_prompt % json.dumps(robot.state), api='ollama')
        print(_next)
        input()
        if "GRAB_JOB" in _next:
            robot.state["job"] = requests.post(robot.RSE_url, json.dumps(robot.get_RSE_body()))
            print(robot.state["job"])
        elif "CONTINUE" in _next:
            robot.work()
        else:
            time.sleep(1)
