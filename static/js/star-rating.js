let stars = document.querySelectorAll(".star-rating__star")
let setMarkSuccessMessage = document.querySelector("#setMarkSuccessMessage")
let submitButton = document.querySelector(".button-ui")

for (let i = 0; i < stars.length; i++) {
    let selectedMark = document.querySelector("#selectedMark")

    stars[i].onmouseover = function(event) {
        let starNum = event.target.getAttribute("data-star-num")

        for (let j = 0; j < starNum; j++) {
            stars[j].setAttribute("data-state", "selected")
        }

        for (let j = starNum; j < stars.length; j++) {
            stars[j].setAttribute("data-state", "waiting")
        }
    }

    stars[i].onmouseout = function(event) {
        let selectedMarkValue = selectedMark.getAttribute("value")

        for (let j = 0; j < stars.length; j++) {
            if (j < selectedMarkValue) {
                stars[j].setAttribute("data-state", "selected")
            }
            else {
                stars[j].setAttribute("data-state", "waiting")
            }
        }
    }

    stars[i].onclick = function(event) {
        let starNum = event.target.getAttribute("data-star-num")

        selectedMark.setAttribute("value", starNum)
        submitButton.removeAttribute("disabled")
    }
}

submitButton.onclick = function() {
    setMarkSuccessMessage.removeAttribute("hidden")
}