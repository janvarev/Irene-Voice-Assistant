import os
import traceback

import time
from threading import Timer

import sounddevice as sound_device
import soundfile as sound_file

from jaa import JaaCore

version = "4.0"

# main VACore class

class VACore(JaaCore):
    def __init__(self):
        JaaCore.__init__(self)

        self.timers = [-1,-1,-1,-1,-1,-1,-1,-1]
        self.timersFuncUpd = [None,None,None,None,None,None,None,None]
        self.timersFuncEnd = [None,None,None,None,None,None,None,None]
        self.timersDuration = [0,0,0,0,0,0,0,0]

        self.commands = {
        }

        self.ttss = {
        }

        # more options
        self.mpcHcPath = ""
        self.mpcIsUse = False
        self.mpcIsUseHttpRemote = False

        self.isOnline = False
        self.version = version

        self.voiceAssNames = []

        self.ttsEngineId = ""

        self.logPolicy = ""
        self.tmpdir = "temp"
        self.tmpcnt = 0

        self.lastSay = ""
        self.remoteTTS = "none"
        self.remoteTTSResult = None

        self.context = None
        self.contextTimer = None
        self.contextTimerLastDuration = 0

        import mpcapi.core
        self.mpchc = mpcapi.core.MpcAPI()



    def init_with_plugins(self):
        self.init_plugins(["core"])
        if self.isOnline:
            print("VoiceAssistantCore v{0}: run online".format(version))
        else:
            print("VoiceAssistantCore v{0}: run OFFLINE".format(version))
        print("TTS engines: ",self.ttss.keys())
        print("Commands list: ",self.commands.keys())
        print("Assistant names: ",self.voiceAssNames)

        self.setup_assistant_voice()

    # ----------- process plugins functions ------
    def process_plugin_manifest(self,modname,manifest):
        # is req online?
        plugin_req_online = True
        if "require_online" in manifest:
            plugin_req_online = manifest["require_online"]

        # adding commands from plugin manifest
        if "commands" in manifest: # process commands
            for cmd in manifest["commands"].keys():
                if not self.isOnline and plugin_req_online:
                    # special processing
                    self.commands[cmd] = self.stub_online_required
                else:
                    # normal add command
                    self.commands[cmd] = manifest["commands"][cmd]

        # adding tts engines from plugin manifest
        if "tts" in manifest: # process commands
            for cmd in manifest["tts"].keys():
                self.ttss[cmd] = manifest["tts"][cmd]

    def stub_online_required(self,core,phrase):
        self.play_voice_assistant_speech(self.plugin_options("core")["replyOnlineRequired"])

    # ----------- text-to-speech functions ------

    def setup_assistant_voice(self):
        self.ttss[self.ttsEngineId][0](self)

    def play_voice_assistant_speech(self,text_to_speech:str):
        self.lastSay = text_to_speech
        if self.remoteTTS == "none": # no remote tts, do locally anything
            self.remoteTTSResult = "" # anywhere, set it ""

            if self.ttss[self.ttsEngineId][1] != None:
                self.ttss[self.ttsEngineId][1](self,text_to_speech)
            else:
                tempfilename = self.get_tempfilename()+".wav"
                #print('Temp TTS filename: ', tempfilename)
                self.tts_to_filewav(text_to_speech,tempfilename)
                self.play_wav(tempfilename)
                if os.path.exists(tempfilename):
                    os.unlink(tempfilename)

        if self.remoteTTS == "saytxt": # return only last say txt
            self.remoteTTSResult = text_to_speech

        if self.remoteTTS == "saywav":
            tempfilename = self.get_tempfilename()+".wav"

            self.tts_to_filewav(text_to_speech,tempfilename)
            #self.play_wav(tempfilename)
            import base64

            with open(tempfilename, "rb") as wav_file:
                encoded_string = base64.b64encode(wav_file.read())

            if os.path.exists(tempfilename):
                os.unlink(tempfilename)

            self.remoteTTSResult = {"wav_base64":encoded_string}


    def say(self,text_to_speech:str): # alias for play_voice_assistant_speech
        self.play_voice_assistant_speech(text_to_speech)

    def tts_to_filewav(self,text_to_speech:str,filename:str):
        if len(self.ttss[self.ttsEngineId]) > 2:
            self.ttss[self.ttsEngineId][2](self,text_to_speech,filename)
        else:
            print("File save not supported by this TTS")

    def get_tempfilename(self):
        self.tmpcnt += 1
        return self.tmpdir+"/vacore_"+str(self.tmpcnt)

    # -------- main function ----------

    def execute_next(self,command,context):
        if context == None:
            context = self.commands

        if isinstance(context,dict):
            pass
        else:
            # it is function to call!
            #context(self,command)
            self.context_clear()
            self.call_ext_func_phrase(command,context)
            return

        try:
            # первый проход - ищем полное совпадение
            for keyall in context.keys():
                keys = keyall.split("|")
                for key in keys:
                    if command == key:
                        rest_phrase = ""
                        next_context = context[keyall]
                        self.execute_next(rest_phrase,next_context)
                        return

            # второй проход - ищем частичное совпадение
            for keyall in context.keys():
                keys = keyall.split("|")
                for key in keys:
                    if command.startswith(key):
                        rest_phrase = command[(len(key)+1):]
                        next_context = context[keyall]
                        self.execute_next(rest_phrase,next_context)
                        return


            # if not founded
            if self.context == None:
                # no context
                self.say(self.plugin_options("core")["replyNoCommandFound"])
            else:
                # in context
                self.say(self.plugin_options("core")["replyNoCommandFoundInContext"])
                # restart timer for context
                if self.contextTimer != None:
                    self.context_set(self.context,self.contextTimerLastDuration)
        except Exception as err:
            print(traceback.format_exc())

    # ----------- timers -----------
    def set_timer(self, duration, timerFuncEnd, timerFuncUpd = None):
        # print "Start set_timer!"
        curtime = time.time()
        for i in range(len(self.timers)):
            if self.timers[i] <= 0:
                # print "Found timer!"
                self.timers[i] = curtime+duration  #duration
                self.timersFuncEnd[i] = timerFuncEnd
                print("New Timer ID =", str(i), ' curtime=', curtime, 'duration=', duration, 'endtime=', self.timers[i])
                return i
        return -1  # no more timer valid

    def clear_timer(self, index, runEndFunc=False):
        if runEndFunc and self.timersFuncEnd[index] != None:
            self.call_ext_func(self.timersFuncEnd[index])
        self.timers[index] = -1
        self.timersDuration[index] = 0
        self.timersFuncEnd[index] = None

    def clear_timers(self): # not calling end function
        for i in range(len(self.timers)):
            if self.timers[i] >= 0:
                self.timers[i] = -1
                self.timersFuncEnd[i] = None

    def _update_timers(self):
        curtime = time.time()
        for i in range(len(self.timers)):
            if(self.timers[i] > 0):
                if curtime >= self.timers[i]:
                    print("End Timer ID =", str(i), ' curtime=', curtime, 'endtime=', self.timers[i])
                    self.clear_timer(i,True)

    # --------- calling functions -----------

    def call_ext_func(self,funcparam):
        if isinstance(funcparam,tuple): # funcparam =(func, param)
            funcparam[0](self,funcparam[1])
        else: # funcparam = func
            funcparam(self)

    def call_ext_func_phrase(self,phrase,funcparam):
        if isinstance(funcparam,tuple): # funcparam =(func, param)
            funcparam[0](self,phrase,funcparam[1])
        else: # funcparam = func
            funcparam(self,phrase)

    # ------- play wav from subfolder ----------
    def play_wav(self,wavfile):
        filename = os.path.dirname(__file__)+"/"+wavfile

        #filename = 'timer/Sounds/Loud beep.wav'
        # now, Extract the data and sampling rate from file
        data_set, fsample = sound_file.read(filename, dtype = 'float32')
        sound_device.play(data_set, fsample)
        # Wait until file is done playing
        status = sound_device.wait()

    # -------- raw txt running -----------------
    def run_input_str(self,voice_input_str,func_before_run_cmd = None): # voice_input_str - строка распознавания голоса, разделенная пробелами
                # пример: "ирина таймер пять"
        if self.logPolicy == "all":
            if self.context == None:
                print("Input: ",voice_input_str)
            else:
                print("Input (in context): ",voice_input_str)

        try:
            voice_input = voice_input_str.split(" ")
            #callname = voice_input[0]
            haveRun = False
            if self.context == None:
                for ind in range(len(voice_input)):
                    callname = voice_input[ind]

                    if callname in self.voiceAssNames: # найдено имя ассистента
                        if self.logPolicy == "cmd":
                            print("Input (cmd): ",voice_input_str)


                        command_options = " ".join([str(input_part) for input_part in voice_input[(ind+1):len(voice_input)]])

                        # running some cmd before run cmd
                        if func_before_run_cmd != None:
                            func_before_run_cmd()


                        #context = self.context
                        #self.context_clear()
                        self.execute_next(command_options, None)
                        haveRun = True
                        break
            else:
                if self.logPolicy == "cmd":
                    print("Input (cmd in context): ",voice_input_str)

                # running some cmd before run cmd
                if func_before_run_cmd != None:
                    func_before_run_cmd()

                self.execute_next(voice_input_str, self.context)
                haveRun = True

        except Exception as err:
            print(traceback.format_exc())

        return haveRun

    # ------------ context handling functions ----------------

    def context_set(self,context,duration = None):
        if duration == None:
            duration = 10

        self.context_clear()

        self.context = context
        self.contextTimerLastDuration = duration
        self.contextTimer = Timer(duration,self._context_clear_timer)
        self.contextTimer.start()

    #def _timer_context
    def _context_clear_timer(self):
        print("Context cleared after timeout")
        self.contextTimer = None
        self.context_clear()

    def context_clear(self):
        self.context = None
        if self.contextTimer != None:
            self.contextTimer.cancel()
            self.contextTimer = None


