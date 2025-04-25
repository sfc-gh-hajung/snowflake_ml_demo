import streamlit as st # Import python packages
from snowflake.snowpark.context import get_active_session

from snowflake.core import Root

import pandas as pd
import json

pd.set_option("max_colwidth",None)

### Default Values
NUM_CHUNKS = 3 # Num-chunks provided as context. Play with this to check how it affects your accuracy

# service parameters
CORTEX_SEARCH_DATABASE = "SALES_INTELLIGENCE"
CORTEX_SEARCH_SCHEMA = "DATA"
CORTEX_SEARCH_SERVICE = "HAEBI_CORTEX_SERVICE"
######
######

# columns to query in the service
COLUMNS = [
    "TRANSCRIPT_TEXT"
]

session = get_active_session()
root = Root(session)                         

svc = root.databases[CORTEX_SEARCH_DATABASE].schemas[CORTEX_SEARCH_SCHEMA].cortex_search_services[CORTEX_SEARCH_SERVICE]
   
### Functions
     
def config_options():

    st.sidebar.selectbox('Select your model:',('mistral-large2', 'llama3.1-70b',
                        'llama3.1-8b', 'snowflake-arctic'), key="model_name")

    # categories = session.sql("select category from docs_chunks_table group by category").collect()

    # cat_list = ['ALL']
    # for cat in categories:
    #     cat_list.append(cat.CATEGORY)
            
    # st.sidebar.selectbox('Select what products you are looking for', cat_list, key = "category_value")

    # st.sidebar.expander("Session State").write(st.session_state)

def get_similar_chunks_search_service(query):

    if st.session_state.category_value == "ALL":
        response = svc.search(query, COLUMNS, limit=NUM_CHUNKS)
    else: 
        filter_obj = {"@eq": {"category": st.session_state.category_value} }
        response = svc.search(query, COLUMNS, filter=filter_obj, limit=NUM_CHUNKS)

    st.sidebar.json(response.json())
    
    return response.json()  

def create_prompt (myquestion):
    
    if st.session_state.rag == 1:
        prompt_context = get_similar_chunks_search_service(myquestion)
  
        prompt = f"""
           You are an expert chat assistance that extracs information from the CONTEXT provided
           between <context> and </context> tags.
           When ansering the question contained between <question> and </question> tags
           be concise and do not hallucinate. 
           If you don´t have the information just say so.
           Only anwer the question if you can extract it from the CONTEXT provideed.
           
           Do not mention the CONTEXT used in your answer.
    
           <context>          
           {prompt_context}
           </context>
           <question>  
           {myquestion}
           </question>
           Answer: 
           """

        json_data = json.loads(prompt_context)

        relative_paths = set(item['relative_path'] for item in json_data['results'])
        
    else:     
        prompt = f"""[0]
         'Question:  
           {myquestion} 
           Answer: '
           """
        relative_paths = "None"
        
    return prompt, relative_paths

def complete(myquestion):

    prompt, relative_paths =create_prompt (myquestion)

    cmd = """
            select snowflake.cortex.complete(?, ?) as response
          """
    
    df_response = session.sql(cmd, params=[st.session_state.model_name, prompt]).collect()
    return df_response, relative_paths

def main():
    
    st.title(f":speech_balloon: Chat Assistant with Snowflake Cortex Search")
    
    config_options()

    st.session_state.rag = st.sidebar.checkbox('Use your own documents as context?')

    question = st.text_input("Enter question", placeholder="What was the initial call with tech corp about?", label_visibility="collapsed")

    if question:
        response, relative_paths = complete(question)        
        res_text = response[0].RESPONSE
        st.markdown(res_text)

                
if __name__ == "__main__":
    main()