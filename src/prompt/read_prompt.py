def prompt(topic):
    with open(f"src/prompt/{topic}.md", "r") as f:
        return f.read()

def system_prompt(topic):
    with open(f"src/prompt/system/{topic}.md", "r") as f:
        return f.read()