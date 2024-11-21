import openai
import Dobby.Scripts.config as config
import csv
import os

openai.api_key = config.OPENAI_API_KEY
action_embeddings = {}
if os.path.exists(config.EMBEDDINGS_FILE):
    with open(config.EMBEDDINGS_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            action_embeddings[row[0]] = [float(i) for i in row[1:]]

class Predicate:
    def __init__(self, default):
        self.default = default
        self.is_true = default

    def reset(self):
        self.is_true = self.default


# used to store dependencies and effects
class Action:
    def __init__(
        self,
        name,
        pos_dependencies=[],
        pos_outcomes=[],
        neg_dependencies=[],
        neg_outcomes=[],
        action_function=None,
        require_response=True
    ):
        self.name = name
        self.pos_dependencies = pos_dependencies
        self.neg_dependencies = neg_dependencies
        self.pos_outcomes = pos_outcomes
        self.neg_outcomes = neg_outcomes
        self.action_function = action_function
        self.require_response = require_response

        # check for cached embedding
        if self.name in action_embeddings:
            self.embedding = action_embeddings[self.name]
        else:
            self.embedding = openai.Embedding.create(
                input=name, engine="text-embedding-ada-002"
            )["data"][0]["embedding"]
            with open(config.EMBEDDINGS_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                row = [self.name]
                row.extend(self.embedding)
                writer.writerow(row)

    def is_valid(self):
        for pd in self.pos_dependencies:
            if not pd.is_true:
                return False

        for nd in self.neg_dependencies:
            if nd.is_true:
                return False

        return True

    def result(self):
        for po in self.pos_outcomes:
            po.is_true = True

        for no in self.neg_outcomes:
            no.is_true = False

    def execute_action(self):
        print ("executed action " + self.name)
        if self.action_function != None:
            self.action_function()
        """mess_pos = (-3.826, 4.153, -0.566)
        go_to_pos(mess_pos)"""
