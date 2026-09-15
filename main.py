from src.agent.rag_agent import RagAgent


def main():
    print("Hr Policy Assistant [type 'exit' to quit)\n")
    agent = RagAgent()

    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        answer = agent.ask(question)
        print(f"\nAssistant: {answer}\n")



if __name__ == "__main__":
    
    main()
