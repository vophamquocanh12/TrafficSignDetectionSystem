let countChart = null;
let latestTimeline = [];

function updateChart() {
  fetch("/chart_data")
    .then((res) => res.json())
    .then((data) => {
      latestTimeline = data.timeline || [];

      const allLabels = [
        "Đường người đi bộ cắt ngang",
        "Trẻ em",
        "Công trường",
        "Giao nhau với đường ưu tiên",
        "Giao nhau có tín hiệu đèn",
        "Đường giao nhau",
      ];

      const labelColors = {
        "Đường người đi bộ cắt ngang": "#0cc112",
        "Trẻ em": "#f500f5",
        "Công trường": "#ff1d0d",
        "Giao nhau với đường ưu tiên": "#2196f3",
        "Giao nhau có tín hiệu đèn": "#9c27b0",
        "Đường giao nhau": "#795548",
      };

      const labels = allLabels;
      const values = allLabels.map((label) => data.counts[label] || 0);
      const colors = allLabels.map((label) => labelColors[label]);

      const maxValue = Math.max(...values, 5);
      const suggestedMax = Math.ceil(maxValue + 2);

      if (!countChart) {
        const ctx = document.getElementById("countChart").getContext("2d");

        countChart = new Chart(ctx, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [
              {
                label: "Số lần nhận diện",
                data: values,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1,
              },
            ],
          },
          options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            animation: false,

            interaction: {
              mode: "nearest",
              intersect: true,
            },

            hover: {
              mode: "nearest",
              intersect: true,
            },

            plugins: {
              legend: {
                display: false,
              },
              tooltip: {
                enabled: true,
                mode: "nearest",
                intersect: true,
                callbacks: {
                  title: function (context) {
                    return context[0].label;
                  },
                  label: function (context) {
                    const label = context.label;
                    const count = context.parsed.x;

                    const items = latestTimeline.filter(
                      (item) => item.class_name === label,
                    );

                    const result = [
                      "Tổng số lần: " + count,
                      "Các lần nhận diện:",
                    ];

                    items.slice(-10).forEach((item, index) => {
                      result.push("Lần " + (index + 1) + ": " + item.datetime);
                    });

                    return result;
                  },
                },
              },
            },
          },
        });
      } else {
        countChart.data.labels = labels;
        countChart.data.datasets[0].data = values;
        countChart.data.datasets[0].backgroundColor = colors;
        countChart.data.datasets[0].borderColor = colors;
        countChart.options.scales.x.suggestedMax = suggestedMax;
        countChart.update();
      }
    });
}

setInterval(updateChart, 2000);
