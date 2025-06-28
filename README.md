# OpenCopilot - PikoAi

**Your AI-Powered Command-Line Companion!**

PikoAi powered by the OpenCopilot framework, transforms your terminal into an intelligent assistant. Seamlessly integrate AI into your daily workflow to automate tasks, conduct research, interact with web services, and much more. Stop switching contexts and let your copilot handle the heavy lifting, right from your command line.

Install it using a single pip command
```bash
pip install pikoai
```
---

## ✨ See It In Action!

Watch a glimpse of OpenCopilot's capabilities:

![OpenCopilot Demo](public/ter_web_demo.gif)

This demo showcases how OpenCopilot can understand your requests, interact with web pages, and provide you with the information you need, all within your terminal.

---

## 🚀 Core Features

- **LLM-Powered Task Automation:** Leverages cutting-edge Large Language Models to understand your natural language prompts and orchestrate complex task execution.
- **Multi-Provider Support:** Flexibility to choose and switch between various LLM providers such as Mistral, Groq, OpenAI, Anthropic, and Gemini.
- **Extensible Tool System:** Equip your AI agent with a growing library of custom tools to interact with files, system details, web content, and more.
- **Versatile Execution Modes:**
  - **Conversational Mode:** Engage in an interactive dialogue to collaboratively accomplish tasks.
  - **One-Shot Task Execution:** Directly execute specific tasks with a single, concise command.
- **User-Friendly CLI:** An intuitive command-line interface to manage configurations, tools, API keys, and task execution.
- **Web Interaction:** Browse websites, extract information, and perform web searches directly through the agent.

---

## 🛠️ Getting Started

### **Prerequisites**
- ![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)
- Git (if cloning from source)

### **Installation**

You can install OpenCopilot using pip:

```bash
pip install pikoai
```

Alternatively, to install from source:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Piko-AI/OpenCopilot.git
    ```
2.  **Navigate to the project directory:**
    ```bash
    cd OpenCopilot
    ```
3.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```
    or if you have multiple Python versions:
    ```bash
    python3 -m venv venv
    ```
4.  **Activate the virtual environment:**
    -   **Windows:**
        ```bash
        venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
5.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## ▶️ Running the Application

Once the installation is complete, you can run OpenCopilot from the root directory of the project:

```bash
python Src/cli.py
```
or
```bash
python3 Src/cli.py
```

This will start OpenCopilot in conversational mode. You can also use it for one-shot tasks.

---

## ⚡ One-Shot Task Execution

Execute tasks directly without entering the conversational mode:

```bash
python Src/cli.py --task "Your task description here"
```

You can also set the maximum number of iterations for a task:

```bash
python Src/cli.py --task "Your task description here" --max-iter 5
```

---

## 🤝 Contributing

We welcome contributions! Please feel free to fork the repository, make your changes, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

This project is licensed under the terms of the LICENSE file.
