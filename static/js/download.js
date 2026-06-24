function downloadOutput() {
  fetch("/download")
    .then(async (res) => {
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "Không tải được output");
        return;
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;

      const contentType = res.headers.get("Content-Type");

      if (contentType && contentType.includes("video")) {
        a.download = "output_detect_video.mp4";
      } else {
        a.download = "output_detect_image.jpg";
      }

      document.body.appendChild(a);
      a.click();
      a.remove();

      window.URL.revokeObjectURL(url);
    })
    .catch(() => {
      alert("Lỗi khi tải output");
    });
}
