from flask import Flask, request, render_template, make_response, jsonify
import os
import json
from os import path

import sys
import semantria
import uuid
import time

# the consumer key and secret
consumerKey = "6570874a-e3c3-410b-b300-7ce2d88127db"
consumerSecret = "f8108d2d-4113-4bd1-bfea-30dfb719b4c6"

# Task statuses
TASK_STATUS_UNDEFINED = 'UNDEFINED'
TASK_STATUS_FAILED = 'FAILED'
TASK_STATUS_QUEUED = 'QUEUED'
TASK_STATUS_PROCESSED = 'PROCESSED'

app = Flask(__name__)

# v ugly sry god
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ajax_endpoint', methods=['POST'])
def endpoint_name():
    print("endpoint hit!")
    rawtext = request.get_json()['text']

    # process text using semantic api

    # Creates JSON serializer instance
    serializer = semantria.JsonSerializer()
    # Initializes new session with the serializer object and the keys.
    session = semantria.Session(consumerKey, consumerSecret, serializer, use_compression=True)
    subscription = session.getSubscription()
    initialTexts = []
    results = []
    tracker = {}
    documents = []

    n = 975
    textchunks = [rawtext[i:i+n] for i in range(0, len(rawtext), n)]
    for text in textchunks:
        # Creates a sample document which need to be processed on Semantria
        # Unique document ID
        # Source text which need to be processed
        doc_id = str(uuid.uuid4())
        documents.append({'id': doc_id, 'text': text})
        tracker[doc_id] = TASK_STATUS_QUEUED

        res = session.queueBatch(documents)
        if res in [200, 202]:
            print("{0} documents queued successfully.".format(len(documents)))
            documents = []

    if len(documents):
        res = session.queueBatch(documents)
        if res not in [200, 202]:
            print("Unexpected error!")
            sys.exit(1)
        print("{0} documents queued successfully.".format(len(documents)))

    print("")

    # fix this too
    while len(list(filter(lambda x: x == TASK_STATUS_QUEUED, tracker.values()))):
        time.sleep(0.5)
        print("Retrieving your processed results...")

        response = session.getProcessedDocuments()
        for item in response:
            if item['id'] in tracker:
                tracker[item['id']] = item['status']
                results.append(item)

    print("")

    # print and populate json to return it
    resultDict = {}

    for data in results:
        dataDict = {}

        # Printing of document sentiment score
        print("Document {0} / Sentiment score: {1}".format(data['id'], data['sentiment_score']))

        # Printing of document themes
        if "themes" in data:
            print("Document themes:")
            for theme in data["themes"]:
                print("\t {0} (sentiment: {1})".format(theme['title'], theme['sentiment_score']))

        # Printing of document entities
        if "entities" in data:
            print("Entities:")
            dataDict["entities"] = data["entities"]
            for entity in data["entities"]:
                print("\t {0}: {1} (sentiment: {2})".format(
                    entity['title'], entity['entity_type'], entity['sentiment_score']
                ))

        # Printing the summary
        if "summary" in data:
            print("Summary:")
            dataDict["summary"] = data["summary"]
            print(data["summary"])

        if "relations" in data:
            print("Relationships:")
            dataDict["relationships"] = data["relations"]
            for relation in data["relations"]:
                print("\t {0}: {1}".format(
                    relation['type'], relation['extra']
                ))

        resultDict[data['id']] = dataDict
        print("")

    print("Done!")

    return jsonify(resultDict)

# start the development server using the run() method
if __name__ == "__main__":
    extra_dirs = ['static',]
    extra_files = extra_dirs[:]
    for extra_dir in extra_dirs:
        for dirname, dirs, files in os.walk(extra_dir):
            for filename in files:
                filename = path.join(dirname, filename)
                if path.isfile(filename):
                    extra_files.append(filename)
    app.run(debug=True, port=5000, extra_files=extra_files)
