async function replyWasGiven() {
	const response = await fetch("/replyWasGiven");
}

var Sound = (function () {
    var df = document.createDocumentFragment();
    return function Sound(src) {
        var snd = new Audio(src);
        df.appendChild(snd); // keep in fragment until finished playing
        snd.addEventListener('ended', async function () {df.removeChild(snd); await replyWasGiven(); });
        snd.play();
        return snd;
    }
}());

async function init() {
    const resultsContainer = document.getElementById('recognition-result');
    const partialContainer = document.getElementById('partial');
	const ireneMode = document.getElementById('irenemode');

    partialContainer.textContent = "Loading...";
    
    const channel = new MessageChannel();
    const model = await Vosk.createModel('/webapi_client/model.tar.gz');
    model.registerPort(channel.port1);

    const sampleRate = 48000;
    
    const recognizer = new model.KaldiRecognizer(sampleRate);
    recognizer.setWords(true);

    recognizer.on("result", (message) => {
        const result = message.result;
        // console.log(JSON.stringify(result, null, 2));
        
		/*
        const newSpan = document.createElement('span');
        newSpan.textContent = `${result.text} `;
        resultsContainer.insertBefore(newSpan, partialContainer);
		*/
		resultsContainer.textContent = result.text;
		
		if (result.text != "") {
			const userAction = async () => {
			  var url = '/sendRawTxt?returnFormat='+ireneMode.value+'&rawtxt='+result.text;
			  console.log(url)
			  const response = await fetch(url);
			  const res = await response.json(); //extract JSON from the http response
			  
			  var needReplyWasGiven = false;
			  if ("restxt" in res) {
				 //console.log("ИРИНА: ",res.saytxt)
				 irene_answer.textContent = res.restxt;
				 needReplyWasGiven = true;
			  }
			  if ("wav_base64" in res) {
				 var snd = Sound("data:audio/wav;base64," + res.wav_base64);
				 needReplyWasGiven = false;
			  }
			  
			  if (needReplyWasGiven) {
				  await replyWasGiven()
			  }
			  // do something with myJson
			}
			userAction();	
		}
    });
    recognizer.on("partialresult", (message) => {
        const partial = message.result.partial;

        partialContainer.textContent = partial;
    });
    
    partialContainer.textContent = "Ready";
    
    const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: false,
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            channelCount: 1,
            sampleRate
        },
    });
    
    const audioContext = new AudioContext();
    await audioContext.audioWorklet.addModule('recognizer-processor.js')
    const recognizerProcessor = new AudioWorkletNode(audioContext, 'recognizer-processor', { channelCount: 1, numberOfInputs: 1, numberOfOutputs: 1 });
    recognizerProcessor.port.postMessage({action: 'init', recognizerId: recognizer.id}, [ channel.port2 ])
    recognizerProcessor.connect(audioContext.destination);
    
    const source = audioContext.createMediaStreamSource(mediaStream);
    source.connect(recognizerProcessor);
}

window.onload = () => {
    const trigger = document.getElementById('trigger');
    trigger.onmouseup = () => {
        trigger.disabled = true;
        init();
    };
}