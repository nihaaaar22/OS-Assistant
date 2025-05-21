<p align="center">
  <img src="https://www.python.org/static/community_logos/python-logo-master-v3-TM.png" alt="Python 3.8+" width="200"/>
</p>

# TaskAutomator

**Empower your terminal with AI!**

Just type `ocp` and open a chat with your companion, your copilot. It will search the internet for you, scrape information from sites, help you with projects, do research, and much more. Your system just became a lot more capable. You now have a companion.

---

## 🚀 Core Features

- **LLM-Powered Task Automation:** Utilizes LLMs to understand prompts and orchestrate task execution.
- **Multi-Provider Support:** Seamlessly switch between LLM providers like Mistral, Groq, and OpenAI.
- **Extensible Tool System:** Equip agents with custom tools to interact with various environments and APIs.
- **Flexible Execution Modes:**
  - **Conversational Mode:** Engage in an interactive dialogue to accomplish tasks.
  - **One-Shot Task Execution:** Directly execute specific tasks with a single command.
- **User-Friendly CLI:** A command-line interface to manage configurations, tools, and task execution.

---

## 🛠️ Getting Started

### **Prerequisites**
- ![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)

### **Installation**
Install using pip:

```bash
pip install ocp
```

---

## ⚡ One-Shot Task Execution

```bash
ocp --task "Your task description here"
```

You can set the maximum number of iterations for a task:

```bash
ocp --task "Your task description here" --max-iter 5
```

---

## 🤝 Contributing

We welcome contributions! Please feel free to fork the repository, make your changes, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

This project is licensed under the terms of the LICENSE file