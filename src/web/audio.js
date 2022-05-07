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

function setPlayButtonHighlight(side, index, color) {
    const cmd = `pycmd('play:${side}:${index}')`;
    const soundLink = document.querySelector(`.soundLink[onclick*="${cmd}"]`);
    if (soundLink) {
        soundLink.style.backgroundColor = color;
    }
}

function clearPlayButtonsHighlight() {
    Array.from(document.getElementsByClassName("soundLink")).forEach(e => {
        e.style.backgroundColor = '';
    });
}
