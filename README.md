# **🤖 Chappi-bot**

Chappi-e is a lightweight AI assistant agent built using the ********React architecture******** with [__LangGraph__](__https://docs.langgraph.dev/__). It is designed to reason, plan, and execute actions using tools in a flexible and modular workflow.

---


https://github.com/user-attachments/assets/8b1c4ffb-f1c3-426d-9ac7-77a81d04d991


## **🛠️ Setup**

This project uses [__Poetry__](__https://python-poetry.org/__) for dependency management.

### **1. Clone the repository**

```bash
git clone https://github.com/santiagoahl/chappi-bot.git
cd chappie
````

_### 2. Install dependencies_

Make sure you have Poetry installed. Then run:

```bash
env varibles
sudo apt install ffmpeg
poetry install
```

### **3. Activate the environment**

```bash
poetry shell # Then activate the shown environment with conda or pyenv
```

---

## **🔐 API Keys Required**

To run Chappie, you need valid API keys for the following services:

* [__OpenAI__](__https://platform.openai.com/__)
* [__LangGraph__](__https://www.langgraph.dev/__)
* [__Tavily Search__](__https://docs.tavily.com/__)
* [__LangChain__](__https://www.langchain.com/__) (used for tool wrappers/utilities)

You can provide these via environment variables or a `.env` file.

---

## **🧠 Architecture**

Chappie is a ********React-style agent********, meaning it follows a loop of:

1. ********Reason******** about the query
2. ********Act******** by calling a tool if needed
3. ********Observe******** the result
4. ********Repeat or respond********

The logic is built using ********LangGraph********, which provides a composable and stateful way to define agent workflows.

---

## **🚀 Run the agent**

You can invoke Chappie using:

```bash
python -m src.agents.react
```

---

## **📄 License**

MIT License.


--- 

# TODO

1. Include tutorial to download stockfish ->
```bash
mkdir -p external/chess-modules
curl -L https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64-avx2.tar -o external/chess-modules/stockfish-ubuntu-x86-64-avx2.tar
mkdir -p external/chess-modules/stockfish
tar -xvf external/chess-modules/stockfish-ubuntu-x86-64-avx2.tar -C external/chess-modules/stockfish --strip-components=1
rm external/chess-modules/stockfish-ubuntu-x86-64-avx2.tar
```
2. Change repo name from chappie to chappi-e
Probably use an `init.sh` script

---

# References
- For the Chess tool, we leveraged [board_to_fen](https://github.com/mcdominik/board_to_fen) and [Stockfish 17.1](https://github.com/official-stockfish/Stockfish)

