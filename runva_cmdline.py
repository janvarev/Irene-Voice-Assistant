import time
import traceback

from vacore import VACore

# ------------------- main loop ------------------
if __name__ == "__main__":
    cmd_core = VACore()
    cmd_core.init_with_plugins()
    print("Command-line for VoiceAssistantCore.")
    print("Enter command (user text like 'привет') or 'exit'")

    # почему бы сразу не отладить какую-то команду?
    time.sleep(0.5)
    cmd_core.execute_next("погода", None)

    while True:
        cmd = input("> ")
        if cmd == "exit":
            break

        cmd_core.execute_next(cmd, None)
