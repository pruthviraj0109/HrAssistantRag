from src.agents.rag_agent import RagAgent


def run_policy_agent(rag_agent: RagAgent, question: str) -> dict:

    answer = rag_agent.ask(question)
    return {"agent_response": answer}

