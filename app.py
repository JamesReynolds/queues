#!/usr/bin/python3
"""
Example application that produces counters
"""

from flask import Flask
import json
import random
import math
import collections

application = Flask(__name__)

queues = collections.defaultdict(int)
counters = collections.defaultdict(int)

def advance():
    """
    Advance the counters along a single step
    """
    ## Items in staging /always/ move to plugin straight away
    queues["plugin"] += queues["staged"]
    counters["plugin"] += queues["staged"]
    queues["staged"] = 0

    ## If we're not staging anything, then stage some things
    if queues["staged"] + queues["plugin"] + queues["processed"] == 0:
        take = min(5, queues["upload"])
        queues["staged"] += take
        counters["staged"] += take
        queues["upload"] -= take

    ## If we've finished processing things, then we can output them
    counters["complete"] += queues["processed"]
    queues["processed"] = 0

    ## It takes a certain amount of time to process all items
    if queues["plugin"] > 0 and random.random() < 1 / (1 + queues["plugin"]):
        queues["processed"] += queues["plugin"]
        counters["processed"] += queues["plugin"]
        queues["plugin"] = 0

    ## New arrivals
    upload = math.floor(random.random() * 2)
    queues["upload"] += upload
    counters["upload"] += upload

@application.route("/counters")
def countersimpl():
    """
    Implement the counters endpoint
    """
    advance()
    return json.dumps(counters)

if __name__ == "__main__":
    application.run(host='0.0.0.0')
