import streamlit as st
import asyncio
from council_manager import CouncilManager, CouncilMember, get_default_council
from voice_handler import VoiceHandler
import ollama

# Page Config
st.set_page_config(page_title="LLM Council", page_icon="🏛️", layout="wide")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "council_manager" not in st.session_state:
    st.session_state.council_manager = CouncilManager()

if "voice_handler" not in st.session_state:
    st.session_state.voice_handler = VoiceHandler()

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = False

def get_installed_models():
    try:
        models_info = ollama.list()
        # 'models' key contains a list of dicts
        return [m['name'] for m in models_info['models']]
    except:
        return ["deepseek-r1", "kimi-k2-thinking", "minimax-m2", "gpt-oss:20b"] # Fallback suggestion

# Sidebar Configuration
st.sidebar.title("🏛️ Council Configuration")

# Model Selection
available_models = get_installed_models()

# Add Cloud Models (Requires Internet)
cloud_models = ["kimi-k2-thinking:cloud", "minimax-m2:cloud"]
for m in cloud_models:
    if m not in available_models:
        available_models.append(m)

if not available_models:
    st.sidebar.error("No Ollama models found! Please install Ollama and pull models (see README).")

# Chairman Selection
chairman_index = 0
for i, m in enumerate(available_models):
    if "deepseek-r1" in m:
        chairman_index = i
        break
chairman_model = st.sidebar.selectbox("Chairman Model", available_models, index=chairman_index if available_models else 0)

st.sidebar.subheader("Council Members")
num_members = st.sidebar.slider("Number of Members", 1, 4, 3)

members = []
# Load default high-performance council roles
default_members = get_default_council()

for i in range(num_members):
    st.sidebar.markdown(f"**Member {i+1}**")
    
    # Defaults from our High-Perf list if available
    def_name = default_members[i].name if i < len(default_members) else f"Member {i+1}"
    def_role = default_members[i].role_description if i < len(default_members) else "Help the user."
    def_model_name = default_members[i].model if i < len(default_members) else available_models[0]
    
    # Try to find the suggested model in installed models
    model_index = 0
    for idx, m in enumerate(available_models):
        if def_model_name in m: # partial match e.g. 'kimi-k2' in 'kimi-k2-thinking:latest'
            model_index = idx
            break
            
    m_name = st.sidebar.text_input(f"Name {i+1}", def_name)
    m_model = st.sidebar.selectbox(f"Model {i+1}", available_models, index=model_index if available_models else 0)
    m_role = st.sidebar.text_area(f"Role {i+1}", def_role)
    members.append(CouncilMember(m_name, m_model, m_role))

# Voice Toggle
st.sidebar.markdown("---")
st.session_state.voice_enabled = st.sidebar.checkbox("Enable Voice Response", value=False)

# Main Interface
st.title("🏛️ LLM Council")
st.markdown("Ask a question, and your council of AI agents will debate and synthesize an answer.")

# Display Chat History
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🏛️"):
            st.markdown(message["content"])

# Input Handling
user_input = st.chat_input("What is your question?")
voice_btn = st.sidebar.button("🎙️ Speak Question")

if voice_btn:
    with st.spinner("Listening..."):
        text = st.session_state.voice_handler.listen()
        if text:
            user_input = text
            st.success(f"Heard: {text}")
        else:
            st.error("Could not understand audio.")

if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

    # Process with Council
    st.session_state.council_manager.set_council(members, chairman_model)
    
    # 1. Gather Opinions
    with st.status("The Council is deliberating...", expanded=True) as status:
        st.write("1. Council members are thinking...")
        # Pass history to council members
        council_results = asyncio.run(st.session_state.council_manager.get_council_responses(user_input, st.session_state.messages))
        
        # Show individual opinions in an expander
        with st.expander("View Individual Council Opinions"):
            for res in council_results:
                st.markdown(f"**{res['name']} ({res['model']})**")
                if res['status'] == 'success':
                    st.info(res['content'])
                else:
                    st.error(res['content'])
        
        st.write("2. Chairman is critiquing and synthesizing...")
        # Chairman streaming response
        stream = asyncio.run(st.session_state.council_manager.synthesize(user_input, council_results, st.session_state.messages))
        
        status.update(label="Council has spoken!", state="complete", expanded=False)

    # Stream Chairman's Response
    with chat_container:
        with st.chat_message("assistant", avatar="🏛️"):
            # Stream the response
            response_placeholder = st.empty()
            full_response = ""
            
            # Iterate over the async generator
            async def consume_stream():
                nonlocal full_response
                async for chunk in stream:
                    content = chunk['message']['content']
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            
            asyncio.run(consume_stream())
    
    # Save Assistant Message
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Voice Output (if enabled)
    if st.session_state.voice_enabled:
        with st.spinner("Synthesizing speech..."):
            st.session_state.voice_handler.speak(full_response)
