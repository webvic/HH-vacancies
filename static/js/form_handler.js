document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("searchForm").onsubmit = function(event) {
        event.preventDefault();
        document.getElementById("loading").style.display = "block";

        fetch(this.action, {
            method: "POST",
            body: new FormData(event.target)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Ошибка сервера");
            }
            return response.text();
        })
        .then(data => {
            document.getElementById("loading").style.display = "none";  // Скрываем индикатор
            document.body.innerHTML = data;
        })
        .catch(error => {
            document.getElementById("loading").innerHTML = "<p class='text-danger'>Произошла ошибка!</p>";
            console.error("Ошибка:", error);
        });
    };
});

