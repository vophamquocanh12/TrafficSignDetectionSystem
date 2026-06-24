let currentMode = "none";

let currentVideoId = "";
let currentInputUrl = "";
let currentOutputUrl = "";

let isPaused = false;

function hideAll() {
  document.getElementById("inputImage").style.display = "none";
  document.getElementById("inputStream").style.display = "none";
  document.getElementById("inputVideo").style.display = "none";

  document.getElementById("outputImage").style.display = "none";
  document.getElementById("outputVideo").style.display = "none";
}

function clearAll() {
  hideAll();

  fetch("/stop_camera", {
    method: "POST",
  });

  fetch("/stop_video", {
    method: "POST",
  });

  document.getElementById("inputImage").src = "";
  document.getElementById("inputStream").src = "";
  document.getElementById("outputImage").src = "";

  document.getElementById("imageInput").value = "";
  document.getElementById("videoInput").value = "";

  currentMode = "none";

  document.getElementById("statusText").innerText = "Đã xóa toàn bộ dữ liệu";
}
