// Функция для запуска таймера на основе оставшегося времени
function startCountdown(duration, display) {
    let timer = duration;
    const interval = setInterval(() => {
        const days = Math.floor(timer / (3600 * 24));
        const hours = Math.floor((timer % (3600 * 24)) / 3600);
        const minutes = Math.floor((timer % 3600) / 60);
        const seconds = timer % 60;

        display.innerText = `${days}d ${hours}h ${minutes}m ${seconds}s`;

        if (--timer < 0) {
            clearInterval(interval);
            display.innerText = "Таймер не запущен";
        }
    }, 1000);
}

// Функция загрузки оставшегося времени для комнаты при загрузке страницы
function loadTimers() {
    document.querySelectorAll(".roomID").forEach(roomIDElement => {
        const roomID = roomIDElement.innerText;
        const roomItem = roomIDElement.closest("li");
        const timerElement = roomItem.querySelector(".timer");

        // Запрос оставшегося времени с сервера
        fetch(`/get_subscription/${roomID}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.subscription_end) {
                    const subscriptionEnd = new Date(data.subscription_end);
                    const currentTime = new Date();
                    const remainingTime = Math.floor((subscriptionEnd - currentTime) / 1000);

                    if (remainingTime > 0) {
                        startCountdown(remainingTime, timerElement);
                    } else {
                        timerElement.innerText = "Таймер не запущен";
                    }
                }
            });
    });
}

// Запуск загрузки таймеров при загрузке страницы
document.addEventListener("DOMContentLoaded", loadTimers);

// Event listener для формы добавления новой комнаты
document.getElementById("addRoomForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const roomTitle = document.getElementById("roomTitle").value;
    const payerNickname = document.getElementById("payerNickname").value;
    const roomID = document.getElementById("roomID").value;
    const adminAccounts = Array.from(document.querySelectorAll('.adminAccount')).map(input => input.value);

    if (!roomTitle || !payerNickname || !roomID || adminAccounts.length === 0) {
        alert("Пожалуйста, заполните все поля перед добавлением комнаты.");
        return;
    }

    // Отправка данных на сервер
    fetch("/add_room", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            title: roomTitle,
            room_id: roomID,
            payer_nickname: payerNickname,
            admins: adminAccounts,
            days: 0,
            minutes: 0
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Комната добавлена успешно!");
            location.reload();
        } else {
            alert("Ошибка при добавлении комнаты.");
        }
    })
    .catch(error => console.error("Ошибка:", error));
});

// Event listener для добавления нового поля администратора
document.addEventListener("click", function(event) {
    if (event.target && event.target.id === "addAdmin") {
        const adminList = document.getElementById("adminList");
        const newAdminWrapper = document.createElement("div");
        newAdminWrapper.className = "admin-wrapper";

        const newAdminInput = document.createElement("input");
        newAdminInput.type = "text";
        newAdminInput.className = "adminAccount";
        newAdminInput.placeholder = "@user:matrix.org";
        newAdminInput.required = true;

        newAdminWrapper.appendChild(newAdminInput);
        adminList.appendChild(newAdminWrapper);
    }
});

// Обработчик для кнопок управления комнатами (старт, пауза, продление времени, редактирование, удаление)
document.addEventListener("click", function(event) {
    const roomItem = event.target.closest("li");
    if (!roomItem) return;

    const roomID = roomItem.querySelector(".roomID").innerText;
    const timerElement = roomItem.querySelector(".timer");

    if (event.target.classList.contains("start")) {
        const days = parseInt(prompt("Введите количество дней для подписки")) || 0;
        const minutes = parseInt(prompt("Введите количество минут для подписки")) || 0;

        fetch(`/extend_subscription/${roomID}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ days, minutes })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const remainingTime = (days * 86400) + (minutes * 60);
                startCountdown(remainingTime, timerElement);
                alert("Подписка продлена успешно!");
            } else {
                alert("Ошибка при продлении подписки.");
            }
        });
    } else if (event.target.classList.contains("edit")) {
        const newTitle = prompt("Введите новое название комнаты", roomItem.querySelector(".roomTitle").innerText);
        const newPayerNickname = prompt("Введите новый никнейм плательщика", roomItem.querySelector(".payerNickname").innerText);
        const newAdminAccounts = prompt("Введите новых администраторов (разделите запятой)", roomItem.querySelector(".adminAccounts").innerText);

        fetch(`/update_room/${roomID}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: newTitle,
                payer_nickname: newPayerNickname,
                admins: newAdminAccounts.split(",").map(admin => admin.trim())
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Информация о комнате обновлена успешно!");
                location.reload();
            } else {
                alert("Ошибка при обновлении информации о комнате.");
            }
        })
        .catch(error => console.error("Ошибка:", error));
    } else if (event.target.classList.contains("delete")) {
        if (confirm(`Удалить комнату ${roomID}?`)) {
            fetch(`/delete_room/${roomID}`, {
                method: "DELETE",
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("Комната удалена успешно!");
                    roomItem.remove();
                } else {
                    alert("Ошибка при удалении комнаты.");
                }
            })
            .catch(error => console.error("Ошибка:", error));
        }
    } else if (event.target.classList.contains("update-time")) {
        // Окно для ввода количества дней
        const days = parseInt(prompt("Введите количество дней для продления подписки")) || 0;
        // Окно для ввода количества минут
        const minutes = parseInt(prompt("Введите количество минут для продления подписки")) || 0;

        fetch(`/extend_subscription/${roomID}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ days, minutes })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const remainingTime = (days * 86400) + (minutes * 60); // Переводим дни и минуты в секунды
                startCountdown(remainingTime, timerElement);
                alert("Подписка продлена успешно!");
            } else {
                alert("Ошибка при продлении подписки.");
            }
        })
        .catch(error => console.error("Ошибка:", error));
    }
});
