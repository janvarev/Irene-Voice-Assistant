//
//let stream2 = navigator.mediaDevices.getUserMedia({audio: true});
//let track = stream2.getAudioTracks()[0];
//console.log(track.getCapabilities());
const connStatus = document.getElementById('conn_status');

var Sound = (function () {
    var df = document.createDocumentFragment();
    return function Sound(src) {
        var snd = new Audio(src);
        df.appendChild(snd); // keep in fragment until finished playing
        snd.addEventListener('ended', function () {df.removeChild(snd);});
        snd.play();
        return snd;
    }
}());

var audio_context;
        var recorder;
        var audio_stream;
var isRecording = false

// websockets
url = ""
if(location.protocol == "http:") {
    url += "ws://"
} else {
    url += "wss://"
}
url += location.hostname
url += ":"+location.port
url += "/wsmic"
console.log("WS url:",url)
let socket = new WebSocket(url);

//socket.binaryType = "arraybuffer";

socket.onopen = function(e) {
  //alert("[open] Соединение установлено");
  connStatus.textContent = "Соединение установлено"
};

socket.onmessage = function(event) {
  //console.log(event.data)
  res = JSON.parse(event.data)
  if ("text" in res) {
	  console.log("Recognized:",res.text)

	  /*
	  const userAction = async () => {
		  var url = urlBaseIrene+'sendRawTxt?returnFormat=saytxt&rawtxt='+res.text;
		  console.log(url)
		  const response = await fetch(url);
		  const myJson = await response.json(); //extract JSON from the http response

		  if ("restxt" in myJson) {
			  console.log("ИРИНА:",myJson.restxt)
		  }
		  // do something with myJson
		}
	  userAction();
	  */
  }
  if ("restxt" in res) {
	 //console.log("ИРИНА: ",res.saytxt)
	 irene_answer.innerHTML = res.restxt;
  }
  if ("wav_base64" in res) {
	 //console.log("ИРИНА: ",res.saytxt)
	 //irene_answer.innerHTML = res.wav_base64;
	 //console.
	 var snd = Sound("data:audio/wav;base64," + res.wav_base64);
  }

};

socket.onclose = function(event) {
  if (event.wasClean) {
    alert(`[close] Соединение закрыто чисто, код=${event.code} причина=${event.reason}`);
  } else {
    // например, сервер убил процесс или сеть недоступна
    // обычно в этом случае event.code 1006
    alert('[close] Соединение прервано');
  }
};

socket.onerror = function(error) {
  alert(`[error] ${error.message}`);
};


// мы будем запрашивать разрешение на доступ только к аудио
/*
const constraints = { audio: true, video: false }
let stream = null
navigator.mediaDevices.getUserMedia(constraints)
 .then((_stream) => { stream = _stream })
 // если возникла ошибка, значит, либо пользователь отказал в доступе,
 // либо запрашиваемое медиа-устройство не обнаружено
 .catch((err) => { console.error(`Not allowed or not found: ${err}`) })

let chunks = []
let mediaRecorder = null
let audioBlob = null
*/
document.querySelector('footer').textContent += new Date().getFullYear()


function flushRec() {
	if (isRecording) {
		//console.log("Flush rec")
		recorder.pause(true)
		recorder.resume()
		//recorder.stop()
		//recorder.start()
		//recorder.flush()
		//recorder.encoder.postMessage( { command: "flush" } );


		setTimeout(flushRec,500)
	}
}

async function startRecord() {
 // проверяем поддержку
 if (!navigator.mediaDevices && !navigator.mediaDevices.getUserMedia) {
   return console.warn('Not supported')
 }

 // если запись не запущена
 if (!isRecording) {
   try {

                // Initialize the Recorder Library
                recorder = new Recorder({encoderPath: "waveWorkerMy.js", recordingGain: 3, streamPages: true});

                console.log('Recorder initialised');

                // Start recording !
                //recorder.record();
				recorder.start()
                console.log('Recording...');

				recorder.ondataavailable = function( typedArray ){
					console.log("sending wav...")
					var dataBlob = new Blob( [typedArray], { type: 'audio/wav' } );

					//var fileName = new Date().toISOString() + ".wav";
					  var url = URL.createObjectURL( dataBlob );

					  //var audio = document.createElement('audio');
					  //audio.controls = true;
					  //audio.src = url;
					  const src = URL.createObjectURL(dataBlob)

					 // создаем элемент `audio`
					 //const audioEl = createEl({ tag: 'audio', src, controls: true })

					 //audio_box.append(audioEl)
					 //audioEl.play()
					 // переключаем классы
					 //toggleClass(record_box, 'hide', 'show')


					socket.send(dataBlob);


				}

				setTimeout(flushRec,500)

     isRecording = true
   } catch (e) {
     console.error(e)

   }
   record_btn.innerHTML = "Stop"
 } else {
   // если запись запущена, останавливаем ее
   //mediaRecorder.stop()
			recorder.stop();
            console.log('Stopped recording.');

            // Stop the getUserMedia Audio Stream !
            //audio_stream.getAudioTracks()[0].stop();
			
			//recorder.getBuffer(getBufferCallback)
			//recorder.exportWAV(getBufferCallback)
			//socket.send(buffer);	

   record_btn.innerHTML = "Record"
   isRecording = false
 }
}

record_btn.onclick = startRecord
