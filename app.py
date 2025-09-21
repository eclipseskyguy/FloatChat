import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import plotly.express as px
import folium
from streamlit_folium import st_folium

# Import LangChain components
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents.agent_types import AgentType

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FloatChat",
    page_icon="🌊",
    layout="wide"
)

# --- DATABASE CONNECTION & LLM SETUP ---
load_dotenv()

# Check for keys
if not os.getenv("DATABASE_URL") or not os.getenv("GOOGLE_API_KEY"):
    st.error("🚨 DATABASE_URL or GOOGLE_API_KEY not found. Please check your .env file.")
    st.stop()

# Cache the engine and agent creation so it doesn't run on every interaction
@st.cache_resource
def get_db_engine_and_agent():
    engine = create_engine(os.getenv("DATABASE_URL"))
    db = SQLDatabase(engine=engine)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0, convert_system_message_to_human=True)
    agent_executor = create_sql_agent(
        llm,
        db=db,
        agent_type="openai-tools",
        verbose=True,
        agent_executor_kwargs={"handle_parsing_errors": True}
    )
    return engine, agent_executor

engine, agent_executor = get_db_engine_and_agent()

# --- HELPER FUNCTIONS ---
@st.cache_data
def run_query(query):
    """Runs a SQL query and returns a DataFrame."""
    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection)
    return df

def create_profile_plot(df, y_axis='pressure'):
    """Intelligently creates a plot based on available columns."""
    columns = [col for col in df.columns if col not in ['id', 'float_id', 'timestamp', 'latitude', 'longitude', 'location', 'pressure']]
    if not columns:
        st.warning("No plottable data columns found in the query result.")
        return None

    x_axis = st.selectbox("Select a variable to plot against Pressure", options=columns)
    if x_axis:
        title = f"{x_axis.replace('_', ' ').title()} vs. Pressure"
        labels = {x_axis: x_axis.title(), y_axis: 'Pressure (dbar)'}
        fig = px.line(df, x=x_axis, y=y_axis, title=title, labels=labels)
        fig.update_yaxes(autorange="reversed")
        return fig
    return None

# --- MAIN APPLICATION UI ---
st.title("🌊 FloatChat - ARGO Float Data Explorer")

# Create two tabs for different modes of interaction
tab1, tab2 = st.tabs(["💬 Chat with Data", "🗺️ Explore by Map"])

# --- TAB 1: CHAT INTERFACE ---
with tab1:
    st.header("Ask a Question to the Database")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("e.g., What is the max temperature?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking and querying the database..."):
                try:
                    full_prompt = (
                        f"You are an expert oceanographer's assistant. Based on the user's question, "
                        f"First, think about what you need to do. Then, write and execute a SQL query to get the necessary data. "
                        f"Finally, answer the user's question based on the query results. "
                        f"Question: '{prompt}'"
                    )
                    response = agent_executor.invoke({"input": full_prompt})
                    response_output = response["output"]
                    st.markdown(response_output)
                    st.session_state.messages.append({"role": "assistant", "content": response_output})
                except Exception as e:
                    error_message = f"An error occurred: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

# --- TAB 2: MAP EXPLORER ---
with tab2:
    st.header("Select a Region on the Map to Find Floats")
    
    # Initialize map centered on the Indian Ocean
    m = folium.Map(location=[0, 80], zoom_start=3)

    # Add a drawing tool to the map
    folium.plugins.Draw(
        export=False,
        draw_options={'polyline': False, 'polygon': False, 'circle': False, 'marker': False, 'circlemarker': False}
    ).add_to(m)

    st.info("Use the rectangle tool on the map's left side to draw a box over an area of interest.")

    # Render the map and capture the drawing events
    map_data = st_folium(m, width='100%', height=500)

    # Check if a rectangle was drawn
    if map_data.get("last_active_drawing"):
        bounds = map_data["last_active_drawing"]["geometry"]["coordinates"][0]
        min_lon, min_lat = bounds[0]
        max_lon, max_lat = bounds[2]

        st.subheader("Query Results")
        with st.spinner("Finding floats in the selected area..."):
            # Construct the PostGIS query
            query = f"""
            SELECT DISTINCT float_id, latitude, longitude, timestamp
            FROM argo_measurements
            WHERE ST_Intersects(
                location,
                ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, 4326)
            )
            ORDER BY timestamp DESC;
            """
            
            try:
                result_df = run_query(query)
                
                if not result_df.empty:
                    # Display metrics
                    col1, col2 = st.columns(2)
                    col1.metric("Floats Found", result_df['float_id'].nunique())
                    col2.metric("Total Measurements", len(result_df))
                    
                    # Display the data table
                    st.dataframe(result_df)

                    # Allow user to select a float to plot
                    selected_float = st.selectbox("Select a Float ID to plot its full profile", options=result_df['float_id'].unique())
                    if selected_float:
                        profile_query = f"SELECT * FROM argo_measurements WHERE float_id = '{selected_float}';"
                        profile_df = run_query(profile_query)
                        
                        plot_fig = create_profile_plot(profile_df)
                        if plot_fig:
                            st.plotly_chart(plot_fig, use_container_width=True)

                else:
                    st.warning("No floats found in the selected region.")

            except Exception as e:
                st.error(f"A database error occurred: {e}")