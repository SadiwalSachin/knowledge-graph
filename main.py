from mem0 import Memory
from openai import OpenAI


GEMINI_API_KEY = "AIzaSyCZjhTka-KO5TzC4IVAdpSenJvleALyL6c"

NEO4J_URL = "bolt://localhost:7686"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "njS2OOoIm79URtOkIeg3C7YU5YSkOCCpIPFMTYWrlIY"

QDRANT_HOST = "localhost"

config = {
    "version":"v1.1",
    "embedder" :{
        "provider":"openai",
        "config":{
            "api_key":GEMINI_API_KEY,
            "model":"models/gemini-embedding-exp-03-07"
        }
    },
    "llm":{
         "provider":"google-genai",
        "config":{
            "api_key":GEMINI_API_KEY,
            "model":"gemini-2.0-flash" 
        }
    },
    "vector_store":{
        "provider":"qdrant",
        "config":{
            "host":QDRANT_HOST,
            "port":6333
        }
    },
    "graph_store":{
        "provider":"neo4j",
        "config":{
            "url":NEO4J_URL,
            "username":NEO4J_USERNAME,
            "password":NEO4J_PASSWORD
        }
    }
}

mem_client = Memory.from_config(config)

client = OpenAI(
    api_key=GEMINI_API_KEY,
)

def chat(message):
    
    messages = [
        {"role":"user","content":message}
    ]
    
    result = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=messages
    )
    
    messages.append({
        "role":"assistant",
        "content":result.choices[0].message.content
    })
    
    mem_client.add(messages , user_id="p123")
    
    return result.choices[0].message.content
    
while True:
    message = input(">>")
    print("BOT",chat(message=message))