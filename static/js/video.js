function uploadVideo() {
  if (currentMode === "camera") {
    alert("Ngắt camera trước");
    return;
  }

  if (currentMode === "image") {
    alert("Xóa ảnh trước");
    return;
  }

  currentMode = "video";

  const file = document.getElementById("videoInput").files[0];

  if (!file) {
    alert("Chọn video");
    return;
  }

  const formData = new FormData();
  formData.append("video", file);

  hideAll();

  fetch("/upload_video", {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      currentVideoId = data.video_id;

      currentInputUrl = data.input;
      currentOutputUrl = data.output;

      document.getElementById("inputStream").style.display = "block";

      document.getElementById("outputImage").style.display = "block";

      document.getElementById("inputStream").src =
        currentInputUrl + "&t=" + Date.now();

      document.getElementById("outputImage").src =
        currentOutputUrl + "&t=" + Date.now();

      document.getElementById("statusText").innerText = "Video đang chạy";
    });
}

function pauseVideo() {
  if (!currentVideoId) return;

  if (!isPaused) {
    fetch("/pause_video", {
      method: "POST",
    });

    isPaused = true;

    document.getElementById("statusText").innerText = "Đã tạm dừng video";
  } else {
    fetch("/resume_video", {
      method: "POST",
    });

    isPaused = false;

    document.getElementById("statusText").innerText = "Video tiếp tục";
  }
}

function clearVideo() {
  fetch("/stop_video", {
    method: "POST",
  });

  document.getElementById("videoInput").value = "";

  document.getElementById("inputStream").src = "";
  document.getElementById("outputImage").src = "";

  hideAll();

  currentMode = "none";
}
