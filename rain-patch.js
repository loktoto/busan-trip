(()=>{
const DATES={"Day 1":"6/19 Fri","Day 2":"6/20 Sat","Day 3":"6/21 Sun","Day 4":"6/22 Mon","Day 5":"6/23 Tue"};
const FALLBACK=[
["金海國際機場","雨天無大問題；如果落大雨，直接用的士去酒店，唔好拖行李轉太多站。"],
["酒店","大雨就留酒店附近食早餐，等雨細先出去，避免拖喼濕身。"],
["海雲台傳統市場","市場有部分遮蓋但唔係全室內；大雨可改附近 café / hotel breakfast。"],
["札嘎其","雨天可照行：札嘎其市場大樓、南浦地下街、樂天百貨光復店都順路。"],
["BIFF","大雨就縮短 BIFF / 國際市場，轉南浦地下街 + 樂天光復店，唔使折返。"],
["甘川","中雨以上唔建議慢行山坡；改 ARTE 早入場，甘川縮短做30–45分鐘影相位。"],
["影島大橋","小雨可睇；大雨就改樂天光復店內休息 / 觀景，唔好企戶外等太耐。"],
["ARTE","雨天主力景點；如果甘川取消，就直接加長 ARTE 時間。"],
["廣安里","無人機 show 遇雨 / 強風可能取消；直接改廣安里室內餐廳 / café，或去 Centum City / Spa Land。"],
["遊艇","雨天 / 大風取消，唔好硬上；改室內 café 或直接回酒店。"],
["海雲台海灘","落雨就改 SEA LIFE Busan Aquarium / café；冬柏島濕滑就取消。"],
["海理團路","雨天照去，揀近地鐵 / 的士落車位嘅室內店。"],
["Busan X","如果能見度差，縮短參觀；改去 café / SEA LIFE / 新世界 Centum City。"],
["Beach Train","小雨可照搭；雷雨 / 強風留意停駛，改 Mipo / 青沙浦 café 等候或取消。"],
["青沙浦","濕滑 / 大風就唔行 skywalk，直接去青沙浦室內 café。"],
["Sky Capsule","小雨景色仍可；強風 / 雷雨可能停運，保留 Beach Train / 的士回海雲台方案。"],
["海東龍宮寺","中雨以上縮短 / 取消；改 Busan National Science Museum 或 Lotte Mall Dongbusan，兩個都同區順路。"],
["機張市場","雨天照去，市場 / 餐廳相對可行；建議的士上落車。"],
["Skyline Luge","雨天 / 大風可能停；改 Lotte Mall Dongbusan / Busan National Science Museum，完全順路。"],
["Waveon","雨天可去但海景差；如果已經累，直接返海雲台休息。"],
["田浦","雨天仍可行；用地鐵站 / 地下街連接，減少露天步行。"],
["西面","雨天仍可行；用地鐵站 / 地下街連接，減少露天步行。"],
["最後散步","雨天取消散步，直接 café / 酒店早餐，早少少出機場。"],
["取行李","大雨預多15–20分鐘 call taxi。"],
["出發去金海","雨天 / 塞車就10:00前出發。"]
];
function esc(s){return String(s||"").replace(/[&<>"']/g,m=>m==="&"?"&amp;":m==="<"?"&lt;":m===">"?"&gt;":m==='"'?"&quot;":"&#39;")}
function planFor(text){let f=FALLBACK.find(x=>text.includes(x[0]));return f?f[1]:""}
function patch(){
 if(!document.getElementById("rainPatchStyle")){
  const st=document.createElement("style");st.id="rainPatchStyle";st.textContent=".rainPlanBox{margin-top:10px;border:1px solid rgba(93,173,226,.28);background:linear-gradient(135deg,rgba(29,53,87,.88),rgba(21,59,54,.68));border-radius:16px;padding:11px 12px;color:#edf7ff}.rainPlanBox b{display:block;color:#a7d8ff;font-size:12px;letter-spacing:.05em;margin-bottom:4px}.rainPlanBox div{font-size:14px;line-height:1.45}.rainDate{display:block;font-size:11px;color:var(--muted,#9aa9a3);font-weight:800;margin-top:2px;line-height:1.1}";document.head.appendChild(st);
 }
 document.querySelectorAll("#tabs button,.scroller button,.pill").forEach(btn=>{
  const src=(btn.dataset.t||btn.dataset.day||btn.getAttribute("data-day")||btn.textContent||"").trim();
  const raw=src.startsWith("Day")?src.split(/\s+/).slice(0,2).join(" "):src;
  if(DATES[raw]&&!btn.dataset.rainDate){btn.innerHTML=esc(raw)+"<span class='rainDate'>"+DATES[raw]+"</span>";btn.dataset.rainDate="1";}
 });
 const head=document.querySelector("#head");
 if(head){const raw=head.textContent.trim().split(" · ")[0];if(DATES[raw]&&!head.dataset.rainDate){head.innerHTML=esc(raw)+" <span class='rainDate'>"+DATES[raw]+"</span>";head.dataset.rainDate="1";}}
 document.querySelectorAll(".card").forEach(card=>{
  if(card.classList.contains("restaurant"))return;
  if(card.querySelector(".rainPlanBox"))return;
  const text=card.textContent||"";const p=planFor(text);if(!p)return;
  const box=document.createElement("div");box.className="rainPlanBox";box.innerHTML="<b>☔ Rain Plan</b><div>"+esc(p)+"</div>";
  const body=card.querySelector(".body")||card;const anchor=body.querySelector(".actions")||body.querySelector(".chips")||body.querySelector(".editPanel")||null;
  if(anchor)body.insertBefore(box,anchor);else body.appendChild(box);
 });
}
patch();
new MutationObserver(patch).observe(document.body,{childList:true,subtree:true,characterData:true});
setInterval(patch,1200);
})();