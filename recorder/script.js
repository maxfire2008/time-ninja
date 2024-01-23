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
      mediaRecorder = new RecordRTC(stream, {
        videoBitsPerSecond: 5000000,
      });
      let recordStart;
      let part;

      const [videoTrack] = stream.getVideoTracks();
      if (videoTrack.getCapabilities !== undefined) {
        const capabilities = videoTrack.getCapabilities();
        const settings = videoTrack.getSettings();

        if ("zoom" in settings) {
          const zoomInput = document.getElementById("zoom");
          zoomInput.min = capabilities.zoom.min;
          zoomInput.max = capabilities.zoom.max;
          zoomInput.step = capabilities.zoom.step;
          zoomInput.value = settings.zoom;

          zoomInput.addEventListener("change", async () => {
            await videoTrack.applyConstraints({
              advanced: [{ zoom: zoomInput.value }],
            });
            saveState();
          });

          // zoom out to min
          zoomInput.value = capabilities.zoom.min;
          zoomInput.dispatchEvent(new Event("change"));
        }
      }

      document.getElementById("video").srcObject = stream;

      record.onclick = () => {
        part = 0;
        mediaRecorder.startRecording();
        recordStart = new Date().toISOString();
        console.log(mediaRecorder.state);
        console.log("recorder started");
        record.style.background = "red";
        record.style.color = "black";
        saveState();
      };

      stop.onclick = () => {
        mediaRecorder.stopRecording();
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
        e.data = null;
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
    zoom: document.getElementById("zoom").value,
    mediaRecorderState: mediaRecorder.state,
  };
  localStorage.setItem("state", JSON.stringify(state));
}

function restoreState() {
  const state = JSON.parse(localStorage.getItem("state"));
  if (state) {
    document.getElementById("eventSlug").value = state.eventSlug;
    document.getElementById("zoom").value = state.zoom;
    if (state.mediaRecorderState === "recording") {
      setTimeout(() => {
        document.getElementById("zoom").dispatchEvent(new Event("change"));
        document.getElementById("record").click();
      }, 5000);
    }
  }
}

document.getElementById("eventSlug").addEventListener("change", saveState);
restoreState();
