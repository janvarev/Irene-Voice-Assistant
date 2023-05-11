"""
Jaa.py Plugin Framework
Author: Janvarev Vladislav

Jaa.py - minimalistic one-file plugin framework with no dependencies.
Main functions:
- run all plugins files from "plugins" folder, base on filename
- save each plugin options in "options" folder in JSON text files for further editing

- Plugins
must located in plugins/ folder
must have "start(core)" function, that returns manifest dict
manifest must contain keys "name" and "version"
can contain "default_options"
- if contain - options will be saved in "options" folder and reload instead next time
- if contain - "start_with_options(core,manifest)" function will run with manifest with "options" key
manifest will be processed in "process_plugin_manifest" function if you override it

- Options (for plugins)
are saved under "options" folder in JSON format
created at first run plugin with "default_options"
updated when plugin change "version"

- Example usage:
class VoiceAssCore(JaaCore): # class must override JaaCore
    def __init__(self):
        JaaCore.__init__(self,__file__)
  ...

main = VoiceAssCore()
main.init_plugins(["core"]) # 1 param - first plugins to be initialized
                            # Good if you need some "core" options/plugin to be loaded before others
                            # not necessary starts with "plugin_" prefix

also can be run like

main.init_plugins()

- Requirements
Python 3.5+ (due to dict mix in final_options calc), can be relaxed
"""

import os
import traceback
import json

# here we trying to use termcolor to highlight plugin info and errors during load
try:
    from termcolor import cprint
except Exception as e:
    # not found? making a stub!
    def cprint(p,color=None):
        if color == None:
            print(p)
        else:
            print(str(color).upper(),p)

version = "2.2.0"

class JaaCore:
    def __init__(self,root_file = __file__):
        self.jaaPluginPrefix = "plugin_"
        self.jaaVersion = version
        self.jaaRootFolder = os.path.dirname(root_file)
        self.jaaOptionsPath = self.jaaRootFolder+os.path.sep+"options"
        self.jaaShowTracebackOnPluginErrors = False
        cprint("JAA.PY v{0} class created!".format(version),"blue")

    # ------------- plugins -----------------
    def init_plugins(self, list_first_plugins = []):
        self.plugin_manifests = {}

        # 1. run first plugins first!
        for modname in list_first_plugins:
            self.init_plugin(modname)

        # 2. run all plugins from plugins folder
        from os import listdir
        from os.path import isfile, join
        pluginpath = self.jaaRootFolder+"/plugins"
        files = [f for f in listdir(pluginpath) if isfile(join(pluginpath, f))]

        for fil in files:
            # print fil[:-3]
            if fil.startswith(self.jaaPluginPrefix) and fil.endswith(".py"):
                modfile = fil[:-3]
                self.init_plugin(modfile)



    def init_plugin(self,modname):
        # import
        try:
            mod = self.import_plugin("plugins."+modname)
        except Exception as e:
            self.print_error("JAA PLUGIN ERROR: {0} error on load: {1}".format(modname, str(e)))
            return False

        # run start function
        try:
            res = mod.start(self)
        except Exception as e:
            self.print_error("JAA PLUGIN ERROR: {0} error on start: {1}".format(modname, str(e)))
            return False

        # if plugin has an options
        if "default_options" in res:
            try:
                # saved options try to read
                saved_options = {}
                try:
                    with open(self.jaaOptionsPath+'/'+modname+'.json', 'r', encoding="utf-8") as f:
                        s = f.read()
                    saved_options = json.loads(s)
                    #print("Saved options", saved_options)
                except Exception as e:
                    pass

                res["default_options"]["v"] = res["version"]


                # only string needs Python 3.5
                final_options = {**res["default_options"], **saved_options}

                # if no option found or version is differ from mod version
                if len(saved_options) == 0 or saved_options["v"] != res["version"]:
                    final_options["v"] = res["version"]
                    self.save_plugin_options(modname,final_options)

                res["options"] = final_options

                try:
                    res2 = mod.start_with_options(self,res)
                    if res2 != None:
                        res = res2
                except Exception as e:
                    self.print_error("JAA PLUGIN ERROR: {0} error on start_with_options processing: {1}".format(modname, str(e)))
                    return False

            except Exception as e:
                self.print_error("JAA PLUGIN ERROR: {0} error on options processing: {1}".format(modname, str(e)))
                return False


        # processing plugin manifest
        try:
            # set up name and version
            plugin_name = res["name"]
            plugin_version = res["version"]


            self.process_plugin_manifest(modname,res)

        except Exception as e:
            print("JAA PLUGIN ERROR: {0} error on process startup options: {1}".format(modname, str(e)))
            return False

        self.plugin_manifests[modname] = res

        self.on_succ_plugin_start(modname,plugin_name,plugin_version)
        return True

    def on_succ_plugin_start(self, modname, plugin_name, plugin_version):
        cprint("JAA PLUGIN: {1} {2} ({0}) started!".format(modname, plugin_name, plugin_version))

    def print_error(self,p):
        cprint(p,"red")
        if self.jaaShowTracebackOnPluginErrors:
            traceback.print_exc()

    def import_plugin(self, module_name):
        import sys

        __import__(module_name)

        if module_name in sys.modules:
            return sys.modules[module_name]
        return None

    def save_plugin_options(self,modname,options):
        # check folder exists
        if not os.path.exists(self.jaaOptionsPath):
            os.makedirs(self.jaaOptionsPath)

        str_options = json.dumps(options, sort_keys=True, indent=4, ensure_ascii=False)
        with open(self.jaaOptionsPath+'/'+modname+'.json', 'w', encoding="utf-8") as f:
            f.write(str_options)
            f.close()

    # process manifest must be overrided in inherit class
    def process_plugin_manifest(self,modname,manifest):
        print("JAA PLUGIN: {0} manifest dummy procession (override 'process_plugin_manifest' function)".format(modname))
        return

    def plugin_manifest(self,pluginname):
        if pluginname in self.plugin_manifests:
            return self.plugin_manifests[pluginname]
        return {}

    def plugin_options(self,pluginname):
        manifest = self.plugin_manifest(pluginname)
        if "options" in manifest:
            return manifest["options"]
        return None

    # ------------ gradio stuff --------------
    def gradio_save(self,pluginname):
        print("Saving options for {0}!".format(pluginname))
        self.save_plugin_options(pluginname,self.plugin_options(pluginname))

    def gradio_upd(self, pluginname, option, val):
        options = self.plugin_options(pluginname)

        # special case
        if isinstance(options[option], (list, dict)) and isinstance(val, str):
            import json
            try:
                options[option] = json.loads(val)
            except Exception as e:
                print(e)
                pass
        else:
            options[option] = val
        print(option,val,options)

    def gradio_render_settings_interface(self, title:str="Settings manager", required_fields_to_show_plugin:list=["default_options"]):
        import gradio as gr

        with gr.Blocks() as gr_interface:
            gr.Markdown("# {0}".format(title))
            for pluginname in self.plugin_manifests:
                manifest = self.plugin_manifests[pluginname]

                # calculate if we show plugin
                is_show_plugin = False
                if len(required_fields_to_show_plugin) == 0:
                    is_show_plugin = True
                else:
                    for k in required_fields_to_show_plugin:
                        if manifest.get(k) is not None:
                            is_show_plugin = True

                if is_show_plugin:
                    with gr.Tab(pluginname):
                        gr.Markdown("## {0} v{1}".format(manifest["name"],manifest["version"]))
                        if manifest.get("description") is not None:
                            gr.Markdown(manifest.get("description"))

                        if manifest.get("url") is not None:
                            gr.Markdown("**URL:** [{0}]({0})".format(manifest.get("url")))


                        if "options" in manifest:
                            options = manifest["options"]
                            if len(options) > 1: # not only v
                                text_button = gr.Button("Save options".format(pluginname))
                                #options_int_list = []
                                for option in options:

                                    #gr.Label(label=option)
                                    if option != "v":
                                        val = options[option]
                                        label = option

                                        if manifest.get("options_label") is not None:
                                            if manifest.get("options_label").get(option) is not None:
                                                label = option+": "+manifest.get("options_label").get(option)


                                        if isinstance(val, (bool, )):
                                            gr_elem = gr.Checkbox(value=val,label=label)
                                        elif isinstance(val, (dict,list)):
                                            import json
                                            gr_elem = gr.Textbox(value=json.dumps(val,ensure_ascii=False), label=label)
                                        else:
                                            gr_elem = gr.Textbox(value=val, label=label)

                                        def handler(x,pluginname=pluginname,option=option):
                                            self.gradio_upd(pluginname, option, x)

                                        gr_elem.change(handler, gr_elem, None)

                                def handler_save(pluginname=pluginname):
                                    self.gradio_save(pluginname)

                                text_button.click(handler_save,inputs=None,outputs=None)
                        else:
                            gr.Markdown("_No options for this plugin_")

        return gr_interface


def load_options(options_file=None,py_file=None,default_options={}):
    # 1. calculating options filename
    if options_file == None:
        if py_file == None:
            raise Exception('JAA: Options or PY file is not defined, cant calc options filename')
        else:
            options_file = py_file[:-3]+'.json'

    # 2. try to read saved options
    saved_options = {}
    try:
        with open(options_file, 'r', encoding="utf-8") as f:
            s = f.read()
        saved_options = json.loads(s)
        #print("Saved options", saved_options)
    except Exception as e:
        pass

    # 3. calculating final options

    # only string needs Python 3.5
    final_options = {**default_options, **saved_options}

    # 4. calculating hash from def options to check - is file rewrite needed?
    import hashlib
    hash = hashlib.md5((json.dumps(default_options, sort_keys=True)).encode('utf-8')).hexdigest()

    # 5. if no option file found or hash was from other default options
    if len(saved_options) == 0 or not ("hash" in saved_options.keys()) or saved_options["hash"] != hash:
        final_options["hash"] = hash
        #self.save_plugin_options(modname,final_options)

        # saving in file
        str_options = json.dumps(final_options, sort_keys=True, indent=4, ensure_ascii=False)
        with open(options_file, 'w', encoding="utf-8") as f:
            f.write(str_options)
            f.close()

    return final_options

"""
The MIT License (MIT)
Copyright (c) 2021 Janvarev Vladislav

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the “Software”), to deal 
in the Software without restriction, including without limitation the rights to use, 
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or 
substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""