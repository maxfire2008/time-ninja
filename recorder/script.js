"use strict";

let mediaRecorder;

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
      facingMode: "environment",
    },
  };

  navigator.mediaDevices
    .getUserMedia(constraints)
    .then((stream) => {
      mediaRecorder = new MediaRecorder(stream, {
        videoKeyFrameIntervalDuration: 5,
        videoKeyFrameIntervalCount: 300,
        videoBitsPerSecond: 10000000,
      });
      let recordStart;
      let part = 0;

      document.getElementById("video").srcObject = stream;

      record.onclick = () => {
        mediaRecorder.start(15000);
        recordStart = new Date().toISOString();
        console.log(mediaRecorder.state);
        console.log("recorder started");
        record.style.background = "red";
        record.style.color = "black";
        saveState();
      };

      stop.onclick = () => {
        mediaRecorder.stop();
        console.log(mediaRecorder.state);
        console.log("recorder stopped");
        record.style.background = "";
        record.style.color = "";
        saveState();
      };

      mediaRecorder.ondataavailable = (e) => {
        fetch(
          "/upload/" +
            document.getElementById("eventSlug").value +
            "/" +
            recordStart +
            "/" +
            part,
          {
            method: "POST",
            headers: {
              "Content-Type": e.data.type,
              "Content-Length": e.data.size,
            },
            body: e.data,
          }
        );
        part += 1;
      };
    })
    .catch((err) => {
      console.error(`The following error occurred: ${err}`);
    });
} else {
  alert("getUserMedia not supported on your browser!");
}

function saveState() {
  const eventSlug = document.getElementById("eventSlug").value;
  const state = {
    eventSlug: eventSlug,
    mediaRecorderState: mediaRecorder.state,
  };
  localStorage.setItem("state", JSON.stringify(state));
}

function restoreState() {
  const state = JSON.parse(localStorage.getItem("state"));
  if (state) {
    document.getElementById("eventSlug").value = state.eventSlug;
    if (state.mediaRecorderState === "recording") {
      setTimeout(() => {
        document.getElementById("record").click();
      }, 1000);
    }
  }
}

document.getElementById("eventSlug").addEventListener("change", saveState);
restoreState();
