function playAudioFiles() {
    Array.from(document.getElementsByTagName("audio")).forEach(e => {
        e.play();
    });
}

function resetAudioSpeeed() {
    Array.from(document.getElementsByTagName("audio")).forEach(e => {
        e.playbackRate = 1.0;
    });
}

function addAudioPlaybackRate(step) {
    Array.from(document.getElementsByTagName("audio")).forEach(e => {
        e.playbackRate += step;
    });
}
