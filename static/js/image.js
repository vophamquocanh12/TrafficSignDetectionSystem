function uploadImage() {
  if (currentMode === "camera") {
    alert("Ngắt camera trước");
    return;
  }

  if (currentMode === "video") {
    alert("Xóa video trước");
    return;
  }

  currentMode = "image";

  const file = document.getElementById("imageInput").files[0];

  if (!file) {
    alert("Chọn ảnh");
    return;
  }

  hideAll();

  document.getElementById("inputImage").style.display = "block";

  document.getElementById("inputImage").src = URL.createObjectURL(file);

  const formData = new FormData();
  formData.append("image", file);

  fetch("/upload_image", {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      document.getElementById("outputImage").style.display = "block";

      document.getElementById("outputImage").src =
        data.output + "?t=" + Date.now();

      document.getElementById("statusText").innerText = "Đã nhận diện ảnh";
    });
}

function clearImage() {
  document.getElementById("imageInput").value = "";

  document.getElementById("inputImage").src = "";
  document.getElementById("outputImage").src = "";

  hideAll();

  currentMode = "none";
}
