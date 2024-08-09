document.addEventListener("DOMContentLoaded", function() {
    var button = document.getElementById("sound-button");
    var audio = new Audio("/static/sounds/sound.mp3");

    button.addEventListener("click", function() {
        audio.play();
    });
});
