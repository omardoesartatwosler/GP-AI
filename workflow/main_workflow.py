from typing import TypedDict, Annotated, Sequence, List, Literal
import operator
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.output_parsers import JsonOutputParser

from pydantic import BaseModel
import requests

from dotenv import load_dotenv
import os
import json

# Load .env file
load_dotenv()

# Extract the API key
API_KEY = os.getenv("API_KEY")

CACHE_ID = []

class GlobalState(TypedDict):
    messages : Annotated[BaseMessage, operator.add]
    user_history : list
    config : dict
    user_insights : list
    category_extracted : str = None
    done : bool
    meta_date : str

   

class MainWorkflow:
    llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.0,
    max_retries=2,
    api_key=API_KEY,
    )
    def __init__(self, memory):
        self.checkpointer = memory
        self.graph = self.construct_workflow()
        pass

    def construct_workflow(self):
        workflow = StateGraph(GlobalState)
        
        workflow.add_node('greet_and_ask',self.greet_and_ask)
        workflow.add_node('process_extract_category', self.process_extract_category)

        workflow.add_node("summarize_user_history", self.summarize_user_history)
        workflow.add_node('suggestion_system', self.suggestion_system)


        workflow.add_node('data_retrival', self.data_retrival)
        workflow.add_node('follow_up_question', self.follow_up_question)

        workflow.add_edge(START, 'greet_and_ask')
        workflow.add_edge('greet_and_ask', 'process_extract_category')

        workflow.add_edge('summarize_user_history', 'suggestion_system')
        workflow.add_edge('suggestion_system', 'follow_up_question')

        workflow.add_edge('data_retrival', 'follow_up_question')
        
        workflow.add_conditional_edges('process_extract_category', self.is_category_extracted , {True : "data_retrival" , False : 'process_extract_category' , 'S': 'summarize_user_history'})
        workflow.add_conditional_edges('follow_up_question',self.should_continue,{True : "process_extract_category" , False : 'follow_up_question'})
        graph = workflow.compile(
            checkpointer = self.checkpointer,
            interrupt_before = ['process_extract_category', 'follow_up_question']
        )
        return graph

    def greet_and_ask(self, state):
        print('in greeting')
        message = f"""
        Hello to our shop, are you looking for personalized recommendations or a specific Category?
        """
        return {'messages' : [AIMessage(content = message)]}
    @staticmethod
    def get_all_categories():
        url = os.getenv("CATEGORIES_URL")
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check for errors
            data = response.json()  # Parse JSON response

            # Extract categories if they exist in the response
            if "categories" in data:
                return data["categories"]
            else:
                print("No categories found in the response.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    @staticmethod   
    def get_products_by_category(category):
        base_url = os.getenv("PRODUCTS_BY_CATEGORY_URL")
        url = f"{base_url}/?category={category}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check for HTTP errors
            data = response.json()  # Parse JSON response

            # Extract products if they exist
            if "products" in data:
                return data["products"]
            else:
                print("No products found for this category.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None


    
    def process_extract_category(self, state):
        print('in processing')
        user_message = state['messages'][-1]
        categories = MainWorkflow.get_all_categories()
        system_prompt = f"""
    You are a smart sales assistant working for a shop. We ONLY offer the following categories: {categories}. 
    Your task is to determine what the user is looking for based on their input.
    
    If the user asks for recommendations please return that json:
    category : 'recommend'
    message : <add a message here>

    **Handling User Input:**
    1. **Direct Request for a Category:**
        - If the user directly mentions a specific product or category, match it to the relevant category from our list.
        - If the product or category is not available in our database, inform the user and suggest related categories that may interest them.

    2. **General Inquiry:**
        - If the user asks a general question about what we sell, provide them with a list of available categories.
        - Ask follow-up questions to narrow down their interests and help them decide.

    **Expected Output Fields:**
    - `"category"`: Based on the user's message, provide the most relevant category. If the category cannot be determined, return `"None"`.
    - `"message"`: 
        - If the category is determined successfully, return `"null"`.
        - If the user's request is unclear or the category is unavailable, return a brief, helpful message, followed by a question to guide them further. The message should be concise (maximum 3 short sentences) and aimed at narrowing down the user's intention.

    **Important Notes:**
    - Always return ONLY a valid JSON response with no extra characters, formatting, or explanations.
    - Avoid excessive detail or verbosity. Focus on clarity and conciseness to improve user interaction.
"""


        # prepare the JSON parser
        class CategoryOutput:
            category : str
            message : str
        parser = JsonOutputParser(pydantic_object = CategoryOutput)

        # prepare the messages to the llm
        messages = [SystemMessage(content = system_prompt),user_message]
        ##print(messages)
        # call the llm 
        output = self.llm.invoke(messages)
        
        
        try :
            # if you can parse
            output = parser.invoke(output)
            

            # if we extract the category successfully, only update the state with the category extracted
            if not output['category'] or output['category']=='None':
                return {'category_extracted' : None ,'messages' : [AIMessage(content = output['message'])]}
            else:
                # if we cannot extract the category, update the state with the message :>
                return {"category_extracted" : output['category']}

        except:
            print('couldnot parse')
            # if you cannot parse, return the output as it is
            return {'category_extracted' : None , 'messages' : [output]}

        
        
    def is_category_extracted(self, state) -> bool:
        if not state.get('category_extracted') or state.get('category_extracted') == 'None' or state.get('category_extracted') == 'null':
          return False
        elif 'recommend' in state.get('category_extracted'):
            return "S"
        else :
          return True
        
    
    def summarize_user_history(self, state):
        print("in summarizing")
        if not state['user_history']:
            return {'user_insights' : 'None'}
        
        system_prompt = f"""
        Given {state['user_history']}, extract useful information in that json:

        summary : <add your own insights here>
        most_bought_category : <most bought category from the user_history>
        most_bought_product :  <most bought product from the user_history>
        meta_data : <any other useful data>

        If there are multiple categories with equal total quantity, choose the one that matches the category of the most bought product as the most_bought_category.
        
        Return only a valid JSON with no extra characters

        """

        messages = [SystemMessage(content = system_prompt)]
        output = self.llm.invoke(messages)

        class Insights:
            summary : str
            most_bought_category : str
            most_bought_product : str
            meta_data : str

        parser = JsonOutputParser(pydantic_object = Insights)
        try:
            output_json = parser.invoke(output)
            return {'user_insights' : output_json}
        except:
            return {'user_insights' : output}
        


# Taking into consideration the insights of the user history : {state['user_insights']}
     # it will tell
    def suggestion_system(self, state):
        print('in suggestion')

        if state['user_insights'] == 'None' or not state['user_insights'] or state['user_insights'] == 'null':
            categories = MainWorkflow.get_all_categories()
            system_prompt = f"""
            You are a smart salesperson working for a shop.
            It seems the user has not made any purchases yet, so we don't have personalized suggestions.
        
            However, we have a variety of categories available: {categories}.
            Kindly ask the user if they are interested in any of them
            """
        else:
            data_required =  self.get_products_by_category(state['user_insights']['most_bought_category'])
            system_prompt =  f"""
            You are a smart sales person working for a shop.
            Taking into consideration the insights of the user history : {state['user_insights']}

            And this is the products we are selling of this category : {data_required}
            Tell the user about our products in a nice way, it should only be MAX 3 sentences 
            """

        messages = [SystemMessage(content = system_prompt)] + state['messages']
        output = self.llm.invoke(messages)
        return {'messages' : [output]}
    

    # it will tell
    def data_retrival(self, state):
        print('in retrieval')
        data_required = MainWorkflow.get_products_by_category(state['category_extracted'])
        system_prompt = f"""
        
        you are a smart sales person working for a shop.
        The user asked some questions about this category : {state['category_extracted']}.

        And this is the products we are selling of this category : {data_required}
        Tell the user about our products in a nice way, it should only be MAX 3 sentences 
        """

        messages = [SystemMessage(content = system_prompt)] + state['messages']
        output = self.llm.invoke(messages)
        return {'messages' : [output]}
    
    # wait for user invoke
    def follow_up_question(self, state):
        print('in follow up')
        if state['category_extracted'] != "recommend":
            data_required = MainWorkflow.get_products_by_category(state['category_extracted'])
            system_prompt = f"""
                    You are a smart and friendly sales assistant working for a shop.

                    The user is asking questions about the following product category: **{state['category_extracted']}**

                    Here are the products we currently sell in this category:
                    {data_required}

                    ---

                    Your task:
                    - Engage the user in a helpful, professional, and concise way (maximum 3 sentences).
                    - Always try to answer their questions and provide helpful suggestions **as long as the question relates to the above category or listed products**.
                    - Be proactive in assisting them with product comparisons, features, pricing, or recommendations **within this category**.

                    ---
    
                    Special Rule:
                    Please return that if (and only if) the user  Clearly asks about a **different product category** or  asks questions about **products that are not in the list above**:     
                    category : 'restart' 
                    message : <add a message here>
                    
                    Return only a valid JSON with no extra characters
                    ---

                    """
            
        else:
            data_required =  self.get_products_by_category(state['user_insights']['most_bought_category'])
            system_prompt = f"""
                    You are a smart and friendly sales assistant working for a shop.

                    The user is asking questions about the following product category: **{state['user_insights']['most_bought_category']}**

                    Here are the products we currently sell in this category:
                    {data_required}

                    ---

                    Your task:
                    - Engage the user in a helpful, professional, and concise way (maximum 3 sentences).
                    - Always try to answer their questions and provide helpful suggestions **as long as the question relates to the above category or listed products**.
                    - Be proactive in assisting them with product comparisons, features, pricing, or recommendations **within this category**.

                    ---
    
                    Special Rule:
                    Please return that if (and only if) the user  Clearly asks about a **different product category** or  asks questions about **products that are not in the list above**:     
                    category : 'restart' 
                    message : <add a message here>
                    
                    Return only a valid JSON with no extra characters
                    ---

                    """

        messages = [SystemMessage(content = system_prompt)] + state['messages']
        output = self.llm.invoke(messages)
        content = output.content.strip()
        if content.startswith("{"):
            parsed_output = json.loads(content)
            if parsed_output.get('category')== 'restart' :
                message = f""" Our store offers a wide range of product categories. Could you please clarify which category you're interested in so I can assist you more effectively?"""
                return {"category_extracted" : "restart" , 'messages' : [AIMessage(content = message)]}
        else :
            return {'messages' : [output]}
        
    def should_continue(self, state) -> bool:
        if 'restart' in state.get('category_extracted'):
          return True
        else :
          return False   
    
    def run(self, state : dict):
        '''
        Basically, this is a generator, that returns an iterator of the messages in the internal state
        It should return all messages consequently, but stops when a node is 'stop before' in compile

        take the user's input, create branch and add

        So the Idea here, each call has a thread_id

        If the call is brand new, we want to start a new workflow from the beginning
        so we pass the message as the state in the first argument, creata a  thread object to the new call and pass it as well

        If the call is not new, we want to continue chatting, we can find the tread_id in the cache_ids
        so we pass the message as a branch_and_add, update the state, and run with state = None, and the branch_and_add as the second argument :>
        '''
        
        if state['config'].get('configurable').get('thread_id') in CACHE_ID:
            branch_and_add = self.graph.update_state(state['config'], {"messages" : state['messages']})
            for event in self.graph.stream(None, branch_and_add):
                for v in event.values():
                    yield v
        else:
            CACHE_ID.append(state['config'].get('configurable').get('thread_id'))
            for intermediate_state in self.graph.stream(state, state['config']):
                for messages in intermediate_state.values():
                    yield messages

memory_for_workflow = MemorySaver()
wf = MainWorkflow(memory_for_workflow)
