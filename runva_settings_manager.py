import traceback

from vacore import VACore
import time
import os

if 'GRADIO_ANALYTICS_ENABLED' not in os.environ:
    os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

import gradio as gr

# ------------------- main loop ------------------
if __name__ == "__main__":
    cmd_core = VACore()
    cmd_core.init_with_plugins()
    print("Settings manager for VoiceAssistantCore.")

    gr_int = cmd_core.gradio_render_settings_interface(
        title="Менеджер настроек для голосового помощника Ирины",
        #required_fields_to_show_plugin=["options","description"]
        required_fields_to_show_plugin=["options","description"]
    )
    gr_int.launch(inbrowser=True)
