# Tested on python3.6


import time
import csv
import numpy as np

import os
import sys
import pathlib
import logging

sys.path.append(str(pathlib.Path(os.path.abspath('')).parents[0])+'/topic-analysis/plsa-service/plsa')

from flask import Flask, jsonify, render_template
from flask import make_response
from flask import request
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

app = Flask(__name__)

status_list = [
    'Analysis started.','Preprocessing started.','Preprocessing finished. Topic analysis started.',
    'Topic analysis finished.','Failed.'
]


def render_result_page(data, status_code=None):
    """
    Wrapping function to render the result page template whenever needed
    """
    if status_code is None: 
        return render_template('result_page.html', data=data) 
    else:
        return render_template('result_page.html', data=data), status_code


# '/topic-analysis/api/v1.0/results'
@app.route('/topic-analysis/api/v1.0/results', methods=['GET'])
# @auth.login_required
def results():
    data = {}   # dict containing all variables needed for page rendering

    try:
        # Code to test exception handler for this try
        # a=1/0

        print('In results:', time.strftime("%c"))

        original_handle = request.args['handle']
        handle = request.args['handle'].replace('e','-').replace('d',' ').replace('y','^')
        print("handle =", handle)
    except Exception as e:
        print("error: ", str(e))
        logging.exception("message")

        data["request_error"] = "Request was not fulfilled. Please try again."
        return render_result_page(data, 400)

    # since there was no exception when processing the handle, we can count it is correct at this line
    data['handle'] = original_handle

    try:
        parameters_path = str(pathlib.Path(os.path.abspath('')).parents[0]) + '/appData/plsa/' + 'plsa-parameters/' + handle + '/'
        print(parameters_path)

        with open(parameters_path + 'status.txt', 'r') as f:
            status = f.read().splitlines()
            data['original_status'] = status

        if status[0] not in status_list:    # if status is what we don't expect at all
            data['error'] = 'Analysis ended unexpectedly. Corrupt status file.'
            return render_result_page(data, 500)
            return make_response(jsonify({'Error': 'Analysis ended unexpectedly, corrupt status file or status file not written yet', "error_msg": ''}), 500)
        elif status[0] == status_list[4]:    # if status is failed
            data['error'] = 'Analysis failed. Server problem.'
            return render_result_page(data)
        elif status[0] != 'Topic analysis finished.':   # if status is other than analysis finished
            status_index = status_list.index(status[0])
            progress_step = status_index + 1    # at which progress step is the analysis

            data['progress_step'] = progress_step
            data['progress_text'] = status[0]
            return render_result_page(data)
            return make_response(jsonify({'status':status}), 200)
        else:   # if status is analysis finished
            data['progress_step'] = 4
            data['progress_text'] = status[0]

            with open(parameters_path + 'plsa_topics.txt', 'r') as f:
                topics = f.read().splitlines()

            topic_by_doc = []
            word_by_topic_conditional = []
            logLikelihoods = []
            docs_list = []

            with open(parameters_path + 'topic-by-doc-matirx.csv') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')

                docs_list = next(csv_reader)[1:]

                for row in csv_reader:
                    topic_by_doc.append(list((np.array(row[1:])).astype(np.float)))

            with open(parameters_path + 'topic_probability_pz', 'r') as f:
                topic_probabilities = f.read().splitlines()

                topic_probabilities = list((np.array(topic_probabilities)).astype(np.float))

            with open(parameters_path + 'word_by_topic_conditional.csv') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')

                for row in csv_reader:
                    word_by_topic_conditional.append(list((np.array(row[:-1])).astype(np.float)))

            with open(parameters_path + 'logL.txt', 'r') as f:
                logLikelihoods = f.read().splitlines()

                logLikelihoods = list((np.array(logLikelihoods)).astype(np.float))

            resp = {}
            resp['status'] = status[0]
            resp['total running time in minutes'] = float(status[1])
            resp['docs_list'] = docs_list
            resp['topics'] = topics
            resp['topicByDocMatirx'] = topic_by_doc
            resp['topicProbabilities'] = topic_probabilities
            resp['wordByTopicConditional'] = word_by_topic_conditional
            resp['logLikelihoods'] = logLikelihoods

            data['status'] = status[0]
            data['total_running_time_in_minutes'] = float(status[1])
            data['docs_list'] = docs_list
            data['topics'] = str(topics)[2:-2]
            data['topicByDocMatirx'] = topic_by_doc
            data['topicProbabilities'] = topic_probabilities
            data['wordByTopicConditional'] = word_by_topic_conditional
            data['logLikelihoods'] = logLikelihoods

            return render_result_page(data)
            return make_response(jsonify(resp), 200)


    except Exception as e:
        print("error: ", str(e))
        logging.exception("message")

        # NOT: This line is tested: it throws back error message correctly
        data['error'] = 'Request was not fulfilled. Please try again.'
        return render_result_page(data)
        return make_response(jsonify({'Error': 'Request was not fulfilled. Please try again.', "error_msg": str(e)}), 500)


@app.errorhandler(404)
def not_found(error):
    print ('In not_found:', time.strftime("%c"))
    return make_response(jsonify({'Error': 'Not found'}), 404)


__end__ = '__end__'


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(debug=False,port=4998)
