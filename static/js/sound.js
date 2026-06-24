const soundMap = {
  "Đường người đi bộ cắt ngang": "/static/sound/nguoidibo.mp3",

  "Trẻ em": "/static/sound/treem.mp3",

  "Công trường": "/static/sound/congtruong.mp3",

  "Giao nhau với đường ưu tiên": "/static/sound/duonguutien.mp3",

  "Giao nhau có tín hiệu đèn": "/static/sound/tinhieuden.mp3",

  "Đường giao nhau": "/static/sound/giaonhau.mp3",
};

let audioQueue = [];
let isPlayingAudio = false;

function playNextSound() {
  if (isPlayingAudio || audioQueue.length === 0) return;

  isPlayingAudio = true;

  const sign = audioQueue.shift();

  const audio = new Audio(soundMap[sign]);

  audio.onended = () => {
    isPlayingAudio = false;
    playNextSound();
  };

  audio.play();
}

function checkSoundEvents() {
  fetch("/sound_events")
    .then((res) => res.json())
    .then((data) => {
      data.events.forEach((sign) => {
        audioQueue.push(sign);
      });

      playNextSound();
    });
}

setInterval(checkSoundEvents, 1000);
