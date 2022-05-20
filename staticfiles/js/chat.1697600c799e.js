const id = JSON.parse(document.getElementById("username-id").textContent);
const userAvatar = document.getElementById("user-avatar").textContent;
const url = `ws://${window.location.host}/ws/chat/${id}/`;
const chatSocket = new WebSocket(url);


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
  div3.className = "flex-none w-8 h-8 overflow-hidden rounded-full";
  div4.className = "flex px-4 py-2 text-sm rounded-3xl";
  div2.className = "mt-2 text-xs";

  div3.appendChild(img);
  div4.appendChild(p);
  li.append(div1, div2);

  if (data.other_user_id === id) {
    div1.append(div4);
    li.className = "flex flex-col items-end";
    p.className = "text-gray-900";
    div4.classList.add("bg-[#70A9A1]");
  } else {
    div1.append(div3, div4);
    div4.classList.add("bg-[#9EC1A3]");
    p.className = "text-black";
    li.className = "";
  }

  p.textContent = data.message;
  div2.textContent= currentTime;

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



