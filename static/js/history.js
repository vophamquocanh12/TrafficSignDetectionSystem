function resetHistory() {
  const confirmReset = confirm(
    "Bạn có chắc chắn muốn reset lịch sử và biểu đồ không?"
  );

  if (!confirmReset) {
    return;
  }

  fetch("/reset", {
    method: "POST"
  })
    .then((res) => res.json())
    .then((data) => {
      if (typeof countChart !== "undefined" && countChart) {
        countChart.data.labels = [];
        countChart.data.datasets[0].data = [];
        countChart.update();
      }

      alert(data.message);

      document.getElementById("statusText").innerText =
        "Đã reset lịch sử và biểu đồ";
    });
}