from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from llama_index.llms import OpenAI
from dotenv import load_dotenv
from llama_index.tools import FunctionTool
from llama_index.llms import OpenAI
from llama_index.agent import ReActAgent
from llama_index import StorageContext, load_index_from_storage
from llama_index.vector_stores import AstraDBVectorStore
from llama_index import (
    VectorStoreIndex,
)
from pydantic import BaseModel
from typing import List, Optional
from models import *
import ast
import re
load_dotenv()
import os
profile_path = "../profile/bio.txt"
with open(profile_path, 'r') as file:
    bio_content = file.read()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/generate_text_response")
async def generate_text_response(textInputs: List[TextInput]) -> List[TextResponse]:
    text_input_details = "\n".join([f"{input.name}" for input in textInputs])
    llm = OpenAI(model="gpt-3.5-turbo-0613", temperature=0)
    detailed_prompt = f"""
        Based on the following resume information and input fields:
        {bio_content}

        Input Fields:
        {text_input_details}

        Generate a list of identifier and value pairs in the format of:
        [('identifier1', 'value1'), ('identifier2', 'value2'), ...].
        For each identifier, extract the corresponding value from the resume or input fields. 
        If a value cannot be obtained from the given information, leave a blank string ('').
        For example, if the resume has a name 'John Doe' and an email 'johndoe@example.com', 
        but no phone number, the output should be [('name', 'John Doe'), ('email', 'johndoe@example.com'), ('phone', '')].
    """
    try:
        llm_response = llm.complete(detailed_prompt).text
    except Exception as e: # TODO: Handle specific exceptions
        print(f"Error calling LLM: {e}")
        return []
    try:
        tuples_list = ast.literal_eval(llm_response)
        responses = [TextResponse(identifier=t[0], value=t[1]) for t in tuples_list]
        return responses
    except Exception as e:
        print(f"Error processing LLM response: {e}")
        return []



@app.post("/generate_radio_response")
async def generate_radio_response(radio_buttons: List[RadioButtonGroup]) -> List[RadioResponse]:
    # Prepare the input for the language model
    radio_input_details = "\n".join([f"{group.name}: {', '.join([option.value for option in group.options])}" for group in radio_buttons])
    llm = OpenAI(model="gpt-3.5-turbo-0613", temperature=0)

    detailed_prompt = f"""
    Based on the following resume information and input fields:
    {bio_content}
    And based on the following radio button groups and their options:
    {radio_input_details}

    Determine the most appropriate selection for each group. For example, if the input is:

    'cards[12345][field0]: No, Yes, Maybe'
    'cards[12345][field1]: True, False'

    Then the output should be a list of group names and their selected values in the format of:
    [('cards[12345][field0]', 'Yes'), ('cards[12345][field1]', 'True')].

    Using this format, generate the selections for the provided input.
    """

    try:
        # Get response from the language model
        llm_response = llm.complete(detailed_prompt).text

        # Extract only the list part of the response
        matches = re.search(r"\[\(.*?\)\]", llm_response, re.DOTALL)
        if matches:
            list_str = matches.group(0)
        else:
            raise ValueError("List not found in LLM response")
    except Exception as e:
        print(f"Error processing LLM response: {e}")
        return []

    try:
        # Parse the extracted string into a list of tuples
        tuples_list = ast.literal_eval(list_str)
        responses = [RadioResponse(name=t[0], selectedValue=t[1]) for t in tuples_list]
        return responses
    except Exception as e:
        print(f"Error parsing LLM response list: {e}")
        return []
    

@app.post("/generate_textarea_response")
async def generate_textarea_response(textareas: List[TextareaInput]) -> List[TextareaResponse]:
    ASTRA_DB_APPLICATION_TOKEN = os.environ.get("ASTRA_DB_APPLICATION_TOKEN")
    ASTRA_DB_API_ENDPOINT = os.environ.get("ASTRA_DB_API_ENDPOINT")

    # load resume engine from vector store Astra DB
    def load_resume_query_engine(collection_name: str):
        astra_db_store = AstraDBVectorStore(
            token=ASTRA_DB_APPLICATION_TOKEN,
            api_endpoint=ASTRA_DB_API_ENDPOINT,
            collection_name=collection_name,
            embedding_dimension=1536,
        )
        index = VectorStoreIndex.from_vector_store(vector_store=astra_db_store)
        query_engine = index.as_query_engine()
        return query_engine
    try:
        resume_engine = load_resume_query_engine("bassim_resume")
        def query_resume(prompt):
            """Use this tool to answer questions about a resume, such as name, skills, experiences, Github or LinkedIn links, etc."""
            return resume_engine.query(prompt + """ answer using information using the retrieved context only.""").response

        # TODO: change to automatically extract the job title from the web form. Hardcoded for demo purpose
        def query_cover_letter():
            """Use this tool to generate a cover letter for a job description. Use this tool when an open-ended question is asked, such as 'Additional Information'"""
            prompt = f"""Write a 5 sentence cover letter in first-person highlighting skills and experiences
            that show this person is a great fit for a job with the following description:
            'ML Engineer Vectara Silicon Valley, CA fulltime Vectara is on a mission to provide a scalable platform for neural information retrieval, helping our customers build advanced language understanding into the next generation of software systems. Our stellar team includes CEO Amr Awadallah, cofounder of Cloudera, experts in neural IR, distributed database systems, and search platforms from organizations including Google, Google Research, Elasticsearch, Databricks, and Twilio.\nThis position is with Vectara's machine learning team. You'll be a good fit if:\n-  You have a passion for working on language understanding with deep neural methods\n-  You have prior industry expertise, or have just completed graduate studies in this area\n-  Excited about working in a collaborative team setting\n-  You are open to living and working in Silicon Valley. While we support working from home, you should be open to the idea of working as a team in our office in Palo Alto, California three days a week\nCome help us build the future of information retrieval!\nIdeally, you will have expertise in one or more of the following areas:\n- Experience with multimodal and multilingual implementation\n- Design of dual-encoder models, or transformer based rerankers, or LLMs for information retrieval\n- Experience with a major deep learning toolkit like Pytorch or JAX\n- Design and development of online learning systems\n- Neural approaches to Open domain QA and Zero-shot IR\n- Familiarity with sparse and dense IR methods\n- Machine learning techniques, including, but not limited to, deep learning\nThe following are plusses, but not required:\n- Published research\n- Vector database expertise, including performance measurement and quantization techniques'
            Start and end the letter with '###'. Sign the letter with this person's name. Give the letter back to me, do not evaluate it.
            """
            return resume_engine.query(prompt).response

        resume_tool = FunctionTool.from_defaults(fn=query_resume)
        letter_tool = FunctionTool.from_defaults(fn=query_cover_letter)

        # initialize llm
        llm = OpenAI(model="gpt-3.5-turbo-0613")

        # initialize ReAct agent
        agent = ReActAgent.from_tools([resume_tool, letter_tool], llm=llm, verbose=True)

        response = extract_content_between_hashes(agent.chat("Write a cover letter."))
    except:
        import time
        time.sleep(8)
        response =  """ 
                Dear Hiring Manager,

                I am writing to express my strong interest in the ML Engineer position at Vectara. With my passion for working on language understanding with deep neural methods and my extensive industry experience in data science and machine learning, I believe I would be a great fit for your team.

                Throughout my career, I have gained expertise in predictive modeling, machine learning, and A/B testing. I have successfully developed and productionized models that have surpassed baselines and achieved significant improvements in performance metrics. Additionally, I have experience working in collaborative team settings, as demonstrated by my leadership in mentoring junior data science teams and founding a data science team book club.

                I am excited about the opportunity to contribute to Vectara's mission of providing a scalable platform for neural information retrieval. My technical skills in Python, R, and various machine learning frameworks, along with my knowledge of distributed database systems, make me well-equipped to tackle the challenges of designing and developing online learning systems.

                Living and working in Silicon Valley is something I am open to, and I am eager to work alongside a stellar team of experts in neural IR and search platforms. I am confident that my skills and experiences align perfectly with the requirements of the ML Engineer role at Vectara.

                Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experiences can contribute to the future of information retrieval at Vectara.

                Sincerely,
                Bassim Eledath
"""
    responses = []
    for textarea in textareas:
        identifier = textarea.name or textarea.id
        # Generate a dummy response. You can modify this logic as needed.
        dummy_text = response
        responses.append(TextareaResponse(identifier=identifier, value=dummy_text))
    return responses


def extract_content_between_hashes(text):
    """
    Extracts and returns all content enclosed between '###' in the given text.

    :param text: A string from which to extract content.
    :return: A list of strings that were enclosed between '###'.
    """
    pattern = "###(.*?)###"
    matches = re.findall(pattern, text)
    return matches
