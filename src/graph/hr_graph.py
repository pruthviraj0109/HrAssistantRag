from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session
from langgraph.checkpoint.memory import MemorySaver
from src.graph.state import HRState
from src.agents.supervisor import route_question
from src.agents.policy_agent import run_policy_agent
from src.agents.leave_agent import run_leave_agent
from src.agents.support_agent import run_support_agent
from langchain_core.messages import HumanMessage, AIMessage


def supervisor_node(state: HRState) -> dict:
    try:
        agent = route_question(
            state["question"],
            state.get("messages", []),
        )

        if hasattr(agent, "agent"):
            agent = agent.agent

        valid_agents = {
            "hr_policy",
            "leave_management",
            "employee_support",
        }

        if agent not in valid_agents:
            agent = "employee_support"

        return {
            "selected_agent": agent,
        }

    except Exception as e:
        return {
            "selected_agent": "employee_support",
            "error": str(e),
        }


def route_decision(state: HRState) -> str:
    return state.get("selected_agent", "employee_support")


def build_hr_graph(rag_agent, db: Session):

    def policy_node(state: HRState) -> dict:
        try:
            return run_policy_agent(rag_agent, state["question"])
        except Exception as e:
            return {
                "agent_response": "I could not find this information in the available HR policy documents.",
                "error": str(e),
            }

    def leave_node(state: HRState) -> dict:
        try:
            return run_leave_agent(
                db=db,
                user_id=state["user_id"],
                question=state["question"],
                messages=state.get("messages", []),
            )

        except Exception as e:
            import traceback

            print("LEAVE AGENT ERROR:")
            print(traceback.format_exc())

            return {
                "agent_response": (
                    "I ran into an error handling your leave request. "
                    "Please try again."
                ),
                "error": str(e),
            }

    def support_node(state: HRState) -> dict:
        try:
            result = run_support_agent(state["question"], state.get("messages", []))
        except Exception as e:
            result = {
                "agent_response": "I'm unable to help with that right now — please contact HR directly."
            }

        return result

    def finalize_node(state: HRState) -> dict:
        return {
            "final_answer": state.get(
                "agent_response", "I could not process your request."
            )
        }

    graph = StateGraph(HRState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("hr_policy", policy_node)
    graph.add_node("leave_management", leave_node)
    graph.add_node("employee_support", support_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_decision,
        {
            "hr_policy": "hr_policy",
            "leave_management": "leave_management",
            "employee_support": "employee_support",
        },
    )
    graph.add_edge("hr_policy", "finalize")
    graph.add_edge("leave_management", "finalize")
    graph.add_edge("employee_support", "finalize")
    graph.add_edge("finalize", END)

    checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)
