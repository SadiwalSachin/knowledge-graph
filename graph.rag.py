from langchain_neo4j import GraphCypherQAChain , Neo4jGraph
from openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

import os


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL")

NEO4J_URL = os.getenv("NEO4J_URL")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key= GEMINI_API_KEY,
    temperature = 0
)

graph = Neo4jGraph(
    url=NEO4J_URL,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    enhanced_schema=True,
)

# graph_result = graph.query(
#     """
# CREATE (lina:Person {name: "Lina", role: "girl"})
# CREATE (tom:Person {name: "Tom", role: "historian"})
# CREATE (seraphina:Person {name: "Queen Seraphina", role: "queen"})
# CREATE (amulet:Object {name: "Amulet"})
# CREATE (secrets:Object {name: "Secrets"})
# CREATE (eldoria:Place {name: "Eldoria", type: "village"})
# CREATE (oakTree:Place {name: "Old Oak Tree", type: "tree"})
# CREATE (virelia:Place {name: "Kingdom of Virelia", type: "kingdom"})
# CREATE (ruins:Place {name: "Ruins"})
# CREATE (libraries:Place {name: "Libraries"})
# CREATE (lina)-[:LIVES_IN]->(eldoria)
# CREATE (amulet)-[:FOUND_UNDER]->(oakTree)
# CREATE (oakTree)-[:LOCATED_IN]->(eldoria)

# CREATE (amulet)-[:BELONGED_TO]->(seraphina)
# CREATE (seraphina)-[:RULED]->(virelia)

# CREATE (lina)-[:FRIEND_OF]->(tom)
# CREATE (lina)-[:SHOWED]->(amulet)
# CREATE (tom)-[:RESEARCHED]->(amulet)
# CREATE (lina)-[:JOURNEYED_WITH]->(tom)
# CREATE (lina)-[:DISCOVERED]->(secrets)
# CREATE (tom)-[:DISCOVERED]->(secrets)

# CREATE (lina)-[:TRAVELED_TO]->(ruins)
# CREATE (lina)-[:TRAVELED_TO]->(libraries)
# CREATE (tom)-[:TRAVELED_TO]->(ruins)
# CREATE (tom)-[:TRAVELED_TO]->(libraries)
# """
# )

# print(f"graph result {graph_result}")

# Querying the graph cypher QA

SYSTEM_PROMPT_FOR_CYPHER_QUERY = """
        You are an expert in analyzing the user input and extracting the entities from the input 
        after extracting all input you extract all the relation btw these entites and for that relations
        and entites you generate a cypher query for neo4j graph db
        
        Follow ouput rules :-
            Provide output in the strings
        
        Example -
            input:"My name is sachin sadiwal"
            Output:""
                    MERGE (u:User {userId: "p123"})
                    SET u.name = "Sachin Sadiwal"
                ""
    """
    

def chat(message):  
          
    graph_schema = graph.schema
    
    CYPHER_GENERATION_TEMPLATE = f"""
    You are an expert in Neo4j and Cypher query language.
    Generate a Cypher query to answer the following question based on the graph schema you have 
    graph schema : {graph_schema}
    
    On the basis of these graph schema you have the all nodes and relations now 
    on the user message analyze the user message and analyze the schema and generate the cypher query 
    for the user message what is want 
    
    {message}

    Return ONLY the Cypher query without any explanations, formatting, or code blocks.
    Do not include the word "cypher" at the beginning.
    Do not wrap the query in quotes.
    Do not add markdown formatting.
    """
    
    cypher_generation_prompt = PromptTemplate(
    input_variables=["query", "schema", "context"],
    template=CYPHER_GENERATION_TEMPLATE
    )


    graph_chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        allow_dangerous_requests=True,
        cypher_prompt=cypher_generation_prompt
    )


    graph_result = graph_chain.invoke({"query":message})
   
    # print(f"graph result {graph_result}")
    
    SYSTEM_PROMPT = f"""
        You are a Memory-Aware Fact Extraction Agent, an advanced AI designed to
        systematically analyze input content, extract structured knowledge, and maintain an
        optimized memory store. Your primary function is information distillation
        and knowledge preservation with contextual awareness.

        Tone: Professional analytical, precision-focused, with clear uncertainty signaling
        
        Memory
            {graph_result.get("result")}
    """
       
    messages = [
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":message}
    ]
    
    chat_result = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=messages
    )
    
    messages.append({
        "role":"assistant","content":chat_result.choices[0].message.content
    })
    
    # print(chat_result.choices[0].message.content)
    
    cypher_query_result = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role":"system","content":SYSTEM_PROMPT_FOR_CYPHER_QUERY},
            {"role":"user","content":message}
        ]
    )

    
    raw_query = cypher_query_result.choices[0].message.content
    
    # print(f"raw query generated to store the info in graph provided by the user {raw_query}")
       
    clean_query = raw_query.strip()
    
    if clean_query.startswith('```') and clean_query.endswith('```'):
        clean_query = clean_query[3:-3].strip()
    
    # Remove any surrounding quotes if present
    if (clean_query.startswith('"') and clean_query.endswith('"')) or \
       (clean_query.startswith("'") and clean_query.endswith("'")):
        clean_query = clean_query[1:-1]
    
    # Execute the cleaned query
    try:
        result = graph.query(clean_query)
        # print(f"result after trying to add in graph {result}")
        # Process result
    except Exception as e:
        print(f"Error executing query: {str(e)}")
        
        
    
    return chat_result.choices[0].message.content
    
    
while True:
    message = input(">>") 
    print (f"BOT {chat(message=message)}")
    