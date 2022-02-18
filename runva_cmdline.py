import traceback

from vacore import VACore
import time

# ------------------- main loop ------------------
if __name__ == "__main__":
    cmd_core = VACore()
    cmd_core.init_with_plugins()
    print("Command-line for VoiceAssistantCore.")
    print("Enter command (user text like 'привет') or 'exit'")

    # почему бы сразу не отладить какую-то команду?
    time.sleep(0.5)
    cmd_core.execute_next("погода",None)

    exit(0) # если нужно - закомментируйте и можно будет работать с командной строкой

    while True:
        cmd = input("> ")
        if cmd == "exit":
            break

        cmd_core.execute_next(cmd,None)