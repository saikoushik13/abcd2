# Code Generated by Sidekick is for learning and experimentation purposes only.
from workflow import executor

def main():
    while True:
        user_input = input("Press Enter to run the workflow, or type 'exit' to quit: ")
        if user_input.lower() == "exit":
            break
        initial_state = {
            "analysis_output": "",
            "project_setup_output": "",
            "codegen_output": ""
        }
        result = executor.invoke(initial_state)
        print("Final Workflow State:")
        print(result)

if __name__ == "__main__":
    main()
