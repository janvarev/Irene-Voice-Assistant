class RecognizerAudioProcessor extends AudioWorkletProcessor {
    constructor(options) {
        super(options);
        
        this.port.onmessage = this._processMessage.bind(this);
    }
    
    _processMessage(event) {
        // console.debug(`Received event ${JSON.stringify(event.data, null, 2)}`);
        if (event.data.action === "init") {
            this._recognizerId = event.data.recognizerId;
            this._recognizerPort = event.ports[0];
        }
    }
    
    process(inputs, outputs, parameters) {
        const data = inputs[0][0];
        if (this._recognizerPort && data) {
            // AudioBuffer samples are represented as floating point numbers between -1.0 and 1.0 whilst
            // Kaldi expects them to be between -32768 and 32767 (the range of a signed int16)
            const audioArray = data.map((value) => value * 0x8000);
        
            this._recognizerPort.postMessage(
                {
                    action: "audioChunk",
                    data: audioArray,
                    recognizerId: this._recognizerId,
                    sampleRate, // Part of AudioWorkletGlobalScope
                },
                {
                    transfer: [audioArray.buffer],
                }
            );
        }
        return true;
    }
}

registerProcessor('recognizer-processor', RecognizerAudioProcessor)