const online_user_id = document.getElementById("online-user-id").textContent;
const url2 = `ws://${window.location.host}/ws/${online_user_id}/`;
const p = document.createElement("p");

const wSocket = new WebSocket(url2);

wSocket.onmessage = function (e) {
  const data = JSON.parse(e.data);
  const status_id = data.user_id;
  const status = document.querySelector("#status" + CSS.escape(status_id));

  if (data.message === "True") {
    status.classList.remove("bg-gray-500");
    status.classList.remove("bg-green-500");
    status.classList.add("bg-green-500");
  }
  if (data.message === "False") {
    status.classList.remove("bg-green-500");
    status.classList.remove("bg-gray-500");
    status.classList.add("bg-gray-500");
  }
  
};
