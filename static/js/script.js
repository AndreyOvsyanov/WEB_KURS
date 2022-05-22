let on_accept = document.getElementById("on_accept")
let delet = document.getElementById("delete")

let on_acceptance = document.getElementById("on_acceptance")
let deleted = document.getElementById("deleted")

on_accept.onclick = function() {
    on_acceptance.style.display = "block"
    deleted.style.display = "none"
}

delet.onclick = function() {
    deleted.style.display = "block"
    on_acceptance.style.display = "none"
}