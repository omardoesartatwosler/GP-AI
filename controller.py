from pydantic import BaseModel
from typing import Dict
from langchain_core.messages import HumanMessage
from workflow.main_workflow import wf, GlobalState


# Dictionary to store conversation states per thread ID
state_storage = {}


class HumanInput(BaseModel):
    user_id: int
    user_history : list 
    messages: str
    thread_id: int

class Controller:
    @staticmethod
    async def chatbot_handler(input_data: HumanInput):
        # Retrieve or create a new state based on the thread ID
        try :
            thread_id = input_data.thread_id
            if thread_id not in state_storage:
                state_storage[thread_id] = GlobalState(messages = [])  # Assuming GlobalState initializes the message list

            state = GlobalState(messages = [])
            
            # Integrate the user message into the state
            
            state['messages'] += [HumanMessage(content = input_data.messages)]

            if input_data.user_history:
                state['user_history'] = input_data.user_history
            else:
                state['user_history'] = []
            
            # Initialize configuration
            state['config'] = {'configurable': {'thread_id': thread_id}}

            # Process the conversation, saving intermediate states
            responses = []
            #print("State:",state)
            # Run the workflow, but break if a stop condition is met
            for output in wf.run(state):
                workflow_active = True  # Indicate that the workflow ran
                try:
                    for message in output.get('messages', []):
                        responses.append(message.content)
                except:
                    pass

            # Save the updated state and return the responses
            state_storage[thread_id] = state
            return {"responses": responses}
        except Exception as e :
            print("why")
            return {"responses":[]}
