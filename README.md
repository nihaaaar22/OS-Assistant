Introduction

We have empowerd your terminal with Ai. Just type ocp and open a chat with your companion , your copilot. It will search the internet for you, scrape information from sites, help you with project, do research and what not. Your system just became a lot more capable. You now have a companion.

Core Features

LLM-Powered Task Automation: Utilizes LLMs to understand prompts and orchestrate task execution.
Multi-Provider Support: Seamlessly switch between LLM providers like Mistral, Groq, and OpenAI.
Extensible Tool System: Equip agents with custom tools to interact with various environments and APIs.
Flexible Execution Modes:
Conversational Mode: Engage in an interactive dialogue to accomplish tasks.
One-Shot Task Execution: Directly execute specific tasks with a single command.
User-Friendly CLI: A command-line interface to manage configurations, tools, and task execution.
Getting Started

Prerequisites
Python 3.8+
Git
Installation
Install using pip: bash pip install ocp

Configuration
API Keys: Open Co-Pilot requires API keys for your chosen LLM provider(s).
Create a .env file in the root directory by copying .env.example.
Add your API keys to the .env file (e.g., MISTRAL_API_KEY=your_mistral_api_key).
LLM Provider & Model:
The first time you run the CLI, or by using the command python Src/cli.py --change-model, you'll be prompted to select your desired LLM provider and model. This configuration is saved in config.json.
Running Open Co-Pilot
or
```bash
ocp
```
One-Shot Task Execution:
ocp  --task "Your task description here"
You can set the maximum number of iterations for a task:
ocp --task "Your task description here" --max-iter 5
Contributing

We welcome contributions! Please feel free to fork the repository, make your changes, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

License

This project is licensed under the terms of the LICENSE file." " " You have to make a landing page. This landing page is not like your typical one. The entire landing page is a terminal. The theme goes with the project functinality. Instead of the actual command you can type ocp --feature, ocp --uses, ocp --install. and ouputs information type writing style( use some open source library for this).