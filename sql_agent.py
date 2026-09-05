import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from mock_sqlite_database import MockSQLiteDatabase

load_dotenv()

st.set_page_config(page_title="Relational SQL Data Agent", page_icon="📊", layout="wide")
st.title("📊 Autonomous Relational SQL Database Agent")
st.write("Query your company's transactional SQL databases using simple plain English questions.")

# Securely Check for Groq API key

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    groq_api_key = st.sidebar.text_input("Enter your Groq API key", type="password")
    if not groq_api_key:
        st.warning("Please configure your  Groq API key to initiate data reflections")
        st.stop()
    os.environ["GROQ_API_KEY"] = groq_api_key

mock_db = MockSQLiteDatabase('enterprise.db')

create_db = mock_db.seed_mock_enterprise_database()

# Connect LangChain's SQL abstraction engine to the local DB file
db = SQLDatabase.from_uri("sqlite:///enterprise.db")

st.sidebar.markdown("### 📋 Active Database Schema")

for table in db.get_usable_table_names():
    st.sidebar.info(f"**Table:** {table}")

# Initialize chat log list session values
if "sql_chat_history" not in st.session_state:
    st.session_state.sql_chat_history = []

# Display previous conversation streams
for message in st.session_state.sql_chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def get_schema(_):
    return db.get_table_info()

def run_query(query_text):
    # Clean model output formatting tags if present
    clean_query = query_text.replace("```sql","").replace("```","").strip()
    try:
        return db.run(clean_query)
    except Exception as e:
        return f"Database Execution Error: {str(e)}"
    
# Agent Logic & Execution Pipeline
if user_query := st.chat_input("Ask a data question (e.g., who are our top customers by total spending?)"):
    # Append human question
    st.chat_message("human").markdown(user_query)
    st.session_state.sql_chat_history.append({"role":"human","content": user_query})

    with st.chat_message("assistant"):
        # Setup stream logging expander
        with st.status("Agent executing database reflection...",expanded=True) as status_box:
            
                # 1. Initialize High Reasoning Core LLM
                llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

                # Construct the text-to-sql prompt pipeline
                sql_generation_prompt = ChatPromptTemplate.from_template(
                    "You are an expert database engineer. Given the database schema" \
                    "information below, write a syntactically correct SQLite query to answer the user's question." \
                    "Return ONLY the executable SQL query string. Do not include markdown blocks, text descriptions, or conversational pleasantries.\n\n"
                    "Schema: \n{schema}\n\n"
                    "Question: {question}\n"
                    "SQL Query:"
                )

                # Form the translation chain
                sql_chain = sql_generation_prompt | llm | StrOutputParser()

                # Construct the final user-facing response prompt pipeline
                response_prompt = ChatPromptTemplate.from_template(
                    "You are an enterprise analytics assistant. Given theuser's original question, the generated SQL code used, and the rawreturned database results, compose a clean natural language answer summarizing the findings.\n\n" 
                    "Question: {question}\n"
                    "Generated SQL Code: {query}\n"
                    "Raw DB Results: {result}\n\n"
                    "Response:"
                )

                response_chain = response_prompt | llm | StrOutputParser()

                # Fetch text structure and pass it to generate the raw query string
                generated_sql = sql_chain.invoke({
                    "schema": get_schema(None),
                    "question": user_query
                })

                # Run the string query directly against our database execution layer
                database_results = run_query(generated_sql)

                # Feed results into the final chain compile the natural language answer
                final_output = response_chain.invoke({
                    "question": user_query,
                    "query": generated_sql,
                    "result": database_results
                })

                # Render intermediate thought logs cleanly inside a dropdown expander for transparency
                with st.expander("Inspect Internal Agent Execution Chains"):
                    st.code(generated_sql,language="sql")
                    st.write(f"**Raw Transaction Result:** `{database_results}`")

                # Render core text answer
                st.markdown(final_output)
                st.session_state.sql_chat_history.append({"role":"assistant", "content": final_output})



