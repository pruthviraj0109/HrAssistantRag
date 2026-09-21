from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph.state import HRState
from src.agents.supervisor import route_question
from src.agents.policy_agent import run_policy_agent
from src.agents.leave_agent import run_leave_agent
from src.agents.support_agent import run_support_agent
from src.agents.onboarding_agent import run_onboard_agent

from langchain_core.messages import AIMessage



checkpointer = MemorySaver()


VALID_AGENTS = {
    "hr_policy",
    "leave_management",
    "employee_support",
    "onboarding",
}


def supervisor_node(state: HRState) -> dict:
    try:
        agent = route_question(
            state["question"],
            state.get("messages", []),
        )

        if hasattr(agent, "agent"):
            agent = agent.agent

        if agent not in VALID_AGENTS:
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
   
    if state.get("awaiting_confirmation"):
        return state.get("pending_agent") or "leave_management"
    return state.get("selected_agent", "employee_support")


def build_hr_graph(rag_agent):

    def policy_node(state: HRState) -> dict:
        try:
            return run_policy_agent(rag_agent, state["question"])
        except Exception as e:
            import traceback

            print("POLICY AGENT ERROR:")
            print(traceback.format_exc())

            return {
                "agent_response": (
                    "I could not find this information in the available "
                    "HR policy documents."
                ),
                "error": str(e),
            }

    def leave_node(state: HRState, config) -> dict:
        db = config["configurable"]["db"]
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

    def onboarding_node(state: HRState, config) -> dict:
        db = config["configurable"]["db"]
        try:
            return run_onboard_agent(
                db=db,
                user_id=state["user_id"],
                question=state["question"],
                messages=state.get("messages", []),
            )

        except Exception as e:
            import traceback

            print("ONBOARDING AGENT ERROR:")
            print(traceback.format_exc())

            return {
                "agent_response": (
                    "I ran into an error looking up your onboarding record. "
                    "Please try again."
                ),
                "error": str(e),
            }

    def support_node(state: HRState) -> dict:
        try:
            return run_support_agent(
                state["question"],
                state.get("messages", []),
            )

        except Exception as e:
          
            import traceback

            print("SUPPORT AGENT ERROR:")
            print(traceback.format_exc())

            return {
                "agent_response": (
                    "I'm unable to help with that right now — "
                    "please contact HR directly."
                ),
                "error": str(e),
            }

    def finalize_node(state: HRState) -> dict:
        answer = state.get("agent_response", "I could not process your request.")
        return {
            "final_answer": answer,
            # without this the assistant never sees its own replies, and any
            # follow-up like "say that in one line" has nothing to refer to
            "messages": [AIMessage(content=answer)],
        }

    graph = StateGraph(HRState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("hr_policy", policy_node)
    graph.add_node("leave_management", leave_node)
    graph.add_node("onboarding", onboarding_node)
    graph.add_node("employee_support", support_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_decision,
        {
            "hr_policy": "hr_policy",
            "leave_management": "leave_management",
            "onboarding": "onboarding",
            "employee_support": "employee_support",
        },
    )
    graph.add_edge("hr_policy", "finalize")
    graph.add_edge("leave_management", "finalize")
    graph.add_edge("onboarding", "finalize")
    graph.add_edge("employee_support", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer)