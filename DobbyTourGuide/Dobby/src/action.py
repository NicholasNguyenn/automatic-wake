import data as data
import csv
import os

from openai import OpenAI
client = OpenAI(api_key=data.OPENAI_API_KEY)

action_embeddings = {}
if os.path.exists(data.EMBEDDINGS_FILE):
    with open(data.EMBEDDINGS_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            action_embeddings[row[0]] = [float(i) for i in row[1:]]

# Classes used to store Dobby's current state and action outcomes

# used to store dependencies and effects
class Action:
    def __init__(
        self,
        name,
        action_function=None,
        require_response=True
    ):
        self.name = name
        self.action_function = action_function
        self.require_response = require_response

        # check for cached embedding
        if self.name in action_embeddings:
            self.embedding = action_embeddings[self.name]
        else:
            self.embedding = client.embeddings.create(input=[self.name], model="text-embedding-3-small").data[0].embedding
            with open(data.EMBEDDINGS_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                row = [self.name]
                row.extend(self.embedding)
                writer.writerow(row)

    def execute_action(self):
        print ("executed action " + self.name)
        if self.action_function != None:
            self.action_function()
