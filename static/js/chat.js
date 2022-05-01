const id = JSON.parse(document.getElementById("username-id").textContent);
const userAvatar = document.getElementById("user-avatar").textContent;
const url = `ws://${window.location.host}/ws/chat/${id}/`;
const chatSocket = new WebSocket(url);
const ulLast = document.getElementById("chat-log")
ulLast.lastElementChild.scrollIntoView({
  behavior: "smooth",
  block: "end",
})



chatSocket.onmessage = function (e) {
  let today = new Date();
  const data = JSON.parse(e.data);
  const currentTime = `${today.getHours()}:${today.getMinutes()}`;


  const ul = document.getElementById("chat-log");
  const div1 = document.createElement("div");
  const div2 = document.createElement("div");
  const div3 = document.createElement("div");
  const div4 = document.createElement("div");
  const li = document.createElement("li");
  const p = document.createElement("p");
  const img = document.createElement("img");

  img.src = userAvatar;
  img.alt = "user-avatar";

  div1.className = "flex space-x-2";
  div3.className = "flex-none w-8 h-8 rounded-full overflow-hidden";
  div4.className = "flex rounded-3xl text-sm py-2 px-4";
  div2.className = "text-xs mt-2";

  div3.appendChild(img);
  div4.appendChild(p);
  li.append(div1, div2);

  if (data.other_user_id === id) {
    div1.append(div4);
    li.className = "flex flex-col items-end";
    p.className = "text-gray-900";
    div4.classList.add("bg-sky-400");
  } else {
    div1.append(div3, div4);
    div4.classList.add("bg-gray-400");
    p.className = "text-black";
    li.className = "";
  }

  p.innerHTML = data.message;
  div2.innerHTML = currentTime;

  ul.appendChild(li);

  ul.scrollIntoView({
    behavior: "smooth",
    block: "end",
  });

};



document.getElementById("chat-message-input").onkeyup = (e) => {
  if (e.keyCode === 13) {
    message();
  }
};
function message() {
  const message = document.getElementById("chat-message-input");
  if (message.value.trim() !== "") {
    chatSocket.send(
      JSON.stringify({
        message: message.value,
        id: id,
      })
    );
  }
  message.value = "";
}



