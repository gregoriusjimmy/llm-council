# LLM Council for Windows

This is your personal AI Council application. It uses local AI models (via Ollama) to debate and answer your questions, ensuring higher accuracy and more creative responses than a single AI.

## Prerequisites

Before running the app, you need to install a few things on your Windows PC.

### 1. Install Python
Download and install Python 3.10 or newer from [python.org](https://www.python.org/downloads/).
*   **Important:** During installation, check the box that says **"Add Python to PATH"**.

### 2. Install Ollama
Ollama is the engine that runs the AI models locally for free.
1.  Go to [ollama.com](https://ollama.com) and download the Windows installer.
2.  Run the installer.
3.  Open a Command Prompt (cmd) or PowerShell and run the following commands to download the **Next-Gen Council** models (High Performance):

    ```bash
    # The Chairman (Reasoning Expert)
    ollama pull deepseek-r1

    # The Thinker (Moonshot AI's reasoning model)
    ollama pull kimi-k2-thinking

    # The Agent (Minimax's coding/agent model)
    ollama pull minimax-m2

    # The Generalist (OpenAI's open model)
    ollama pull gpt-oss:20b
    ```
    *Note: These models are large. If you have less than 16GB RAM, stick to smaller models like `llama3` and `gemma:2b`.*

## Installation

1.  Open Command Prompt (cmd) or PowerShell in this folder (`LLM_Council`).
2.  Install the required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If you get an error installing `pyaudio`, you might need to install C++ Build Tools or search for "install pyaudio windows".*

## How to Run

1.  In your terminal/command prompt, run:
    ```bash
    streamlit run app.py
    ```
2.  A browser window will open automatically (usually at `http://localhost:8501`).
3.  You will see the **LLM Council** interface.

## Usage Guide

*   **Council Configuration (Sidebar):**
    *   **Chairman Model:** The smart AI that synthesizes the final answer (Recommended: `deepseek-r1` or `gpt-oss:20b`).
    *   **Members:** Add up to 4 members.
    *   **Models:** Assign a specific AI model to each member.
*   **Voice:**
    *   Toggle "Enable Voice Response" in the sidebar to hear the Chairman speak.
    *   Click "🎙️ Speak Question" to talk to the council instead of typing.

## Troubleshooting
*   **"No Ollama models found"**: Make sure Ollama is running (check your system tray) and you have run `ollama pull <model_name>`.
*   **Voice issues**: Ensure your microphone is set as default in Windows settings.
