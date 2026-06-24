function startCamera() {
  if (currentMode === "image") {
    alert("Vui lòng xóa ảnh trước");
    return;
  }

  if (currentMode === "video") {
    alert("Vui lòng xóa video trước");
    return;
  }

  currentMode = "camera";

  hideAll();

  document.getElementById("inputStream").style.display = "block";
  document.getElementById("outputImage").style.display = "block";

  document.getElementById("inputStream").src = "/camera_raw?t=" + Date.now();

  document.getElementById("outputImage").src = "/camera_detect?t=" + Date.now();

  document.getElementById("statusText").innerText =
    "Đang nhận diện bằng camera";
}

function stopCamera() {
  fetch("/stop_camera", {
    method: "POST",
  })
    .then((res) => res.json())
    .then((data) => {
      document.getElementById("inputStream").src = "";
      document.getElementById("outputImage").src = "";

      hideAll();

      currentMode = "none";

      document.getElementById("statusText").innerText = data.message;
    });
}
