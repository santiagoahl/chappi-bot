# 🤖 Chappie

Chappie is a lightweight AI assistant agent built using the **React architecture** with [LangGraph](https://docs.langgraph.dev/). It is designed to reason, plan, and execute actions using tools in a flexible and modular workflow.

---

![Captura de pantalla 2025-05-16 005150](https://github.com/user-attachments/assets/20c96271-6f72-477a-80b6-89fa72008714)


## 🛠️ Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/chappie.git
cd chappie
````

### 2. Install dependencies

Make sure you have Poetry installed. Then run:

```bash
poetry install
```

### 3. Activate the environment

```bash
poetry shell
```

---

## 🔐 API Keys Required

To run Chappie, you need valid API keys for the following services:

* [OpenAI](https://platform.openai.com/)
* [LangGraph](https://www.langgraph.dev/)
* [Tavily Search](https://docs.tavily.com/)
* [LangChain](https://www.langchain.com/) (used for tool wrappers/utilities)

You can provide these via environment variables or a `.env` file.

---

## 🧠 Architecture

Chappie is a **React-style agent**, meaning it follows a loop of:

1. **Reason** about the query
2. **Act** by calling a tool if needed
3. **Observe** the result
4. **Repeat or respond**

The logic is built using **LangGraph**, which provides a composable and stateful way to define agent workflows.

---

## 🚀 Run the agent

You can invoke Chappie using:

```bash
python -m src.agents.react
```

---

## 📄 License

MIT License.
