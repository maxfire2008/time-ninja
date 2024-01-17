if (navigator.mediaDevices) {
  console.log("getUserMedia supported.");

  const record = document.getElementById("record");
  const stop = document.getElementById("stop");

  const constraints = {
    audio: true,
    video: {
      frameRate: { min: 30, ideal: 240 },
      width: { min: 1280, ideal: 1920 },
      height: { min: 720, ideal: 1080 },
    },
  };
  let chunks = [];

  navigator.mediaDevices
    .getUserMedia(constraints)
    .then((stream) => {
      const mediaRecorder = new MediaRecorder(stream);

      record.onclick = () => {
        mediaRecorder.start();
        console.log(mediaRecorder.state);
        console.log("recorder started");
        record.style.background = "red";
        record.style.color = "black";
      };

      stop.onclick = () => {
        mediaRecorder.stop();
        console.log(mediaRecorder.state);
        console.log("recorder stopped");
        record.style.background = "";
        record.style.color = "";
      };

      mediaRecorder.onstop = (e) => {
        console.log("data available after MediaRecorder.stop() called.");

        const blob = new Blob(chunks, { type: "video/webm" });
        chunks = [];
        console.log("recorder stopped");
      };

      mediaRecorder.ondataavailable = (e) => {
        chunks.push(e.data);
        fetch("/upload", {
          method: "POST",
          body: e.data,
        });
      };
    })
    .catch((err) => {
      console.error(`The following error occurred: ${err}`);
    });
} else {
  alert("getUserMedia not supported on your browser!");
}
