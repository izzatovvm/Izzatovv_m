"""Instagramsiz sinash: python chat.py — terminalda savol yozing, agent bilimlar bazasidan javob beradi."""
import agent

print("Savol yozing (chiqish: Ctrl+C)")
while True:
    try:
        q = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if q:
        print(agent.answer("test", q), "\n")
