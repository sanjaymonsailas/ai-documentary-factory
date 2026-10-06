import * as THREE from 'three';
import './styles.css';

type ZombieType = 'walker' | 'runner' | 'tank';
type GateEffect = { label: string; multiplier?: number; additive?: number };
type LevelData = {
  id: number;
  name: string;
  starting: number;
  speed: number;
  baseHp: number;
  gates: { z: number; left: GateEffect; right: GateEffect }[];
  hazards: { z: number; lane: -1 | 0 | 1; amount: number; label: string }[];
  squads: { z: number; lane: -1 | 0 | 1; amount: number }[];
};

const SAVE_KEY = 'zombie-horde-save-v1';
const LANE_X = [-5.2, 0, 5.2];

const LEVELS: LevelData[] = [
  {
    id: 1, name: 'SUBURBS', starting: 5, speed: 8.7, baseHp: 85,
    gates: [
      { z: 20, left: { label: '×2', multiplier: 2 }, right: { label: '+6', additive: 6 } },
      { z: 43, left: { label: '×3', multiplier: 3 }, right: { label: '×2', multiplier: 2 } },
      { z: 67, left: { label: '+10', additive: 10 }, right: { label: '×4', multiplier: 4 } }
    ],
    hazards: [{ z: 31, lane: 1, amount: 5, label: 'FIRE' }, { z: 56, lane: -1, amount: 10, label: 'BARRIER' }],
    squads: [{ z: 82, lane: 1, amount: 12 }]
  },
  {
    id: 2, name: 'DOWNTOWN', starting: 6, speed: 8.9, baseHp: 125,
    gates: [
      { z: 18, left: { label: '×3', multiplier: 3 }, right: { label: '×2', multiplier: 2 } },
      { z: 39, left: { label: '×5', multiplier: 5 }, right: { label: '-4', additive: -4 } },
      { z: 62, left: { label: '+20', additive: 20 }, right: { label: '×3', multiplier: 3 } }
    ],
    hazards: [{ z: 30, lane: -1, amount: 8, label: 'SPIKES' }, { z: 52, lane: 0, amount: 16, label: 'FIRE' }],
    squads: [{ z: 77, lane: -1, amount: 18 }, { z: 90, lane: 1, amount: 22 }]
  },
  {
    id: 3, name: 'INDUSTRIAL', starting: 8, speed: 9.1, baseHp: 175,
    gates: [
      { z: 17, left: { label: '×2', multiplier: 2 }, right: { label: '×4', multiplier: 4 } },
      { z: 37, left: { label: '×6', multiplier: 6 }, right: { label: '-8', additive: -8 } },
      { z: 59, left: { label: '+30', additive: 30 }, right: { label: '×3', multiplier: 3 } },
      { z: 80, left: { label: '×2', multiplier: 2 }, right: { label: '×5', multiplier: 5 } }
    ],
    hazards: [{ z: 28, lane: 0, amount: 15, label: 'CRUSHER' }, { z: 48, lane: 1, amount: 18, label: 'FIRE' }, { z: 72, lane: -1, amount: 25, label: 'ELECTRIC' }],
    squads: [{ z: 91, lane: 0, amount: 30 }]
  },
  {
    id: 4, name: 'METRO', starting: 10, speed: 9.4, baseHp: 240,
    gates: [
      { z: 17, left: { label: '×3', multiplier: 3 }, right: { label: '×2', multiplier: 2 } },
      { z: 36, left: { label: '×5', multiplier: 5 }, right: { label: '+15', additive: 15 } },
      { z: 58, left: { label: '×2', multiplier: 2 }, right: { label: '×6', multiplier: 6 } },
      { z: 80, left: { label: '+40', additive: 40 }, right: { label: '×3', multiplier: 3 } }
    ],
    hazards: [{ z: 27, lane: -1, amount: 20, label: 'LASER' }, { z: 49, lane: 1, amount: 26, label: 'FIRE' }, { z: 70, lane: 0, amount: 35, label: 'CRUSHER' }],
    squads: [{ z: 89, lane: -1, amount: 35 }, { z: 99, lane: 1, amount: 35 }]
  },
  {
    id: 5, name: 'MILITARY ZONE', starting: 12, speed: 9.7, baseHp: 330,
    gates: [
      { z: 15, left: { label: '×4', multiplier: 4 }, right: { label: '×2', multiplier: 2 } },
      { z: 34, left: { label: '+30', additive: 30 }, right: { label: '×5', multiplier: 5 } },
      { z: 55, left: { label: '×2', multiplier: 2 }, right: { label: '×7', multiplier: 7 } },
      { z: 75, left: { label: '×5', multiplier: 5 }, right: { label: '+50', additive: 50 } }
    ],
    hazards: [{ z: 25, lane: 0, amount: 30, label: 'MINEFIELD' }, { z: 46, lane: -1, amount: 36, label: 'TURRET' }, { z: 66, lane: 1, amount: 45, label: 'AIRSTRIKE' }],
    squads: [{ z: 84, lane: 0, amount: 50 }, { z: 96, lane: -1, amount: 55 }]
  }
];

type SaveData = { level: number; coins: number; startBonus: number; selected: ZombieType; unlocked: ZombieType[] };
const DEFAULT_SAVE: SaveData = { level: 1, coins: 350, startBonus: 0, selected: 'walker', unlocked: ['walker', 'runner', 'tank'] };

function loadSave(): SaveData {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return { ...DEFAULT_SAVE, unlocked: [...DEFAULT_SAVE.unlocked] };
    const parsed = JSON.parse(raw) as Partial<SaveData>;
    return { ...DEFAULT_SAVE, ...parsed, unlocked: parsed.unlocked ?? [...DEFAULT_SAVE.unlocked] };
  } catch { return { ...DEFAULT_SAVE, unlocked: [...DEFAULT_SAVE.unlocked] }; }
}
function saveGame() { localStorage.setItem(SAVE_KEY, JSON.stringify(save)); }

let save = loadSave();
let currentLevel: LevelData = LEVELS[Math.min(save.level - 1, LEVELS.length - 1)];

const root = document.querySelector<HTMLDivElement>('#game')!;
const ui = document.querySelector<HTMLDivElement>('#ui')!;

const scene = new THREE.Scene();
scene.background = new THREE.Color('#9fcdf0');
scene.fog = new THREE.Fog('#9fcdf0', 70, 185);

const camera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 0.1, 280);
camera.position.set(0, 28, -26);

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
root.appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight('#ffffff', '#49635a', 2.1));
const sun = new THREE.DirectionalLight('#ffffff', 3.2);
sun.position.set(-25, 45, 15);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
scene.add(sun);

const world = new THREE.Group();
scene.add(world);

function mat(color: string, roughness = 0.82, metalness = 0) {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness });
}
function box(name: string, size: THREE.Vector3, color: string, pos: THREE.Vector3) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(size.x, size.y, size.z), mat(color));
  mesh.name = name; mesh.position.copy(pos); mesh.castShadow = true; mesh.receiveShadow = true; world.add(mesh); return mesh;
}
function addTree(x: number, z: number, scale = 1) {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.scale.setScalar(scale);
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(.24,.32,2.2,8), mat('#76523b'));
  trunk.position.y=1.1; trunk.castShadow=true; g.add(trunk);
  const crown = new THREE.Mesh(new THREE.IcosahedronGeometry(1.55,1), mat('#5eac4b'));
  crown.position.y=2.8; crown.castShadow=true; g.add(crown);
  world.add(g);
}
function buildWorld() {
  world.clear();
  const grass = box('grass', new THREE.Vector3(60, .35, 185), '#79b46a', new THREE.Vector3(0,-.35,75));
  grass.receiveShadow=true;
  const road = box('road', new THREE.Vector3(18, .16, 185), '#384455', new THREE.Vector3(0,-.1,75));
  road.receiveShadow=true;
  box('sidewalkL', new THREE.Vector3(7,.24,185), '#c7ccd2', new THREE.Vector3(-12.5,-.02,75));
  box('sidewalkR', new THREE.Vector3(7,.24,185), '#c7ccd2', new THREE.Vector3(12.5,-.02,75));
  for (let z=-4; z<170; z+=8) {
    box('lane', new THREE.Vector3(.33,.05,4), '#e2e8ee', new THREE.Vector3(0,.01,z));
  }
  const buildingColors=['#d8765b','#6687af','#d7a44c','#7e6ea4','#5a9a82'];
  for (let z=2; z<168; z+=18) {
    const h=4+((z/18)%3)*1.6;
    const left=box('building',new THREE.Vector3(7,h,12),buildingColors[(z/18)%buildingColors.length|0],new THREE.Vector3(-21,h/2,z+4));
    const right=box('building',new THREE.Vector3(7,h+1.1,12),buildingColors[((z/18)+2)%buildingColors.length|0],new THREE.Vector3(21,(h+1.1)/2,z+4));
    for (const side of [-1,1]) for (let wy=1.6;wy<h;wy+=1.7) {
      for (let wx=-23;wx>=-25;wx-=2.0) box('window',new THREE.Vector3(.08,.75,1.2),'#c7efff',new THREE.Vector3(side<0?wx:-wx,wy,z+0.8));
    }
  }
  for (let z=0;z<170;z+=15) { addTree(-16.5,z+2,.85); addTree(16.5,z+7,.8); }
  for (let z=10;z<150;z+=22) {
    box('lightpoleL',new THREE.Vector3(.13,3.2,.13),'#394552',new THREE.Vector3(-9.5,1.6,z));
    box('lightpoleR',new THREE.Vector3(.13,3.2,.13),'#394552',new THREE.Vector3(9.5,1.6,z+8));
  }
}
buildWorld();

function textSprite(text: string, color = '#ffffff') {
  const canvas = document.createElement('canvas'); canvas.width=512; canvas.height=160;
  const ctx=canvas.getContext('2d')!;
  ctx.clearRect(0,0,512,160); ctx.fillStyle='rgba(10,16,25,.88)'; ctx.roundRect(8,18,496,124,30); ctx.fill();
  ctx.strokeStyle='rgba(255,255,255,.16)'; ctx.lineWidth=6; ctx.stroke();
  ctx.fillStyle=color; ctx.font='900 74px Arial Black, Arial'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(text,256,82);
  const texture=new THREE.CanvasTexture(canvas); texture.colorSpace=THREE.SRGBColorSpace;
  const s=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,transparent:true,depthWrite:false}));
  s.scale.set(5.8,1.8,1); return s;
}

function createGate(z:number, left:GateEffect, right:GateEffect) {
  const g=new THREE.Group(); g.position.z=z;
  for (const [i,e] of [[-1,left],[1,right]] as const) {
    const x=i*5.2;
    const glow = new THREE.Mesh(new THREE.BoxGeometry(8,.22,.8), mat(i<0?'#2eaaff':'#67dc62',.45,.15));
    glow.position.set(x,4,0); g.add(glow);
    box('gatePost',new THREE.Vector3(.42,5.2,.7),'#2b3542',new THREE.Vector3(x-3.35,2.6,z));
    box('gatePost',new THREE.Vector3(.42,5.2,.7),'#2b3542',new THREE.Vector3(x+3.35,2.6,z));
    const s=textSprite(e.label, e.multiplier ? '#d6ff86' : (e.additive && e.additive<0 ? '#ff7a7a' : '#8fd8ff'));
    s.position.set(x,5.8,0); g.add(s);
  }
  world.add(g); return g;
}

function createHazard(z:number,lane:number,label:string) {
  const x=LANE_X[lane+1];
  const base=box('hazard',new THREE.Vector3(4.3,.28,1.7),'#ff6b35',new THREE.Vector3(x,.2,z));
  base.material.emissive.set('#6b220f'); (base.material as THREE.MeshStandardMaterial).emissiveIntensity=.7;
  const s=textSprite(label,'#ffab79'); s.position.set(x,2.5,z); s.scale.set(3.6,1.1,1); world.add(s);
}
function createSquad(z:number,lane:number) {
  const g=new THREE.Group(); g.position.set(LANE_X[lane+1],0,z);
  for(let i=0;i<5;i++){
    const x=(i-2)*.72;
    const body= new THREE.Mesh(new THREE.BoxGeometry(.55,.9,.42), mat('#315a8f')); body.position.set(x,.72,0); body.castShadow=true; g.add(body);
    const head=new THREE.Mesh(new THREE.IcosahedronGeometry(.38,1), mat('#e5b58d')); head.position.set(x,1.48,0); head.castShadow=true; g.add(head);
    const visor=new THREE.Mesh(new THREE.BoxGeometry(.44,.12,.46), mat('#202832')); visor.position.set(x,1.5,-.31); g.add(visor);
  }
  world.add(g);
}

const zombieMeshes: Record<ZombieType, THREE.InstancedMesh> = {} as Record<ZombieType, THREE.InstancedMesh>;
const zombieColors: Record<ZombieType,string> = { walker:'#76b84f', runner:'#9ad65d', tank:'#57773b' };
for (const t of ['walker','runner','tank'] as ZombieType[]) {
  zombieMeshes[t] = new THREE.InstancedMesh(new THREE.CapsuleGeometry(.32,t==='tank'?.65:.55,4,8), mat(zombieColors[t]), 600);
  zombieMeshes[t].castShadow=true; zombieMeshes[t].receiveShadow=true; zombieMeshes[t].count=0; world.add(zombieMeshes[t]);
}

const eye = new THREE.Mesh(new THREE.SphereGeometry(.065,6,6),mat('#10150f'));
const hordeGroup=new THREE.Group(); world.add(hordeGroup);
const hordeAura=new THREE.Mesh(new THREE.RingGeometry(1.5,2.2,40), new THREE.MeshBasicMaterial({color:'#c9ff72',transparent:true,opacity:.2,side:THREE.DoubleSide}));
hordeAura.rotation.x=-Math.PI/2; hordeAura.position.y=.03; hordeGroup.add(hordeAura);

let hordeCount=0;
let hordeZ=0;
let playerX=0;
let runState:'menu'|'playing'|'attacking'|'won'|'lost' = 'menu';
let attackTimer=0;
let baseHp=0;
let baseMax=0;
let lastTime=performance.now();
let gates: THREE.Group[] = [];
let solvedGates=0;
let solvedHazards=0;
let solvedSquads=0;
let shake=0;

function clearDynamic() {
  gates.forEach(g=>world.remove(g));
  gates=[];
  world.children.filter(c=>c.name==='hazard'||c.name==='window'||c.name==='gatePost'||c.name==='building').forEach(()=>{});
  world.children.filter(c=>c.userData.dynamic===true).forEach(c=>world.remove(c));
}
function createBase(hp:number) {
  const g=new THREE.Group(); g.userData.dynamic=true; g.position.set(0,0,124);
  const body=box('base',new THREE.Vector3(11,6,6),'#4a5362',new THREE.Vector3(0,3,0)); body.material.emissive.set('#141a25');
  const roof=box('roof',new THREE.Vector3(13,1,7),'#252d3a',new THREE.Vector3(0,6.5,0));
  const skull=textSprite('☠ BASE','#ffdb68'); skull.position.set(0,6.9,.1); skull.scale.set(4.8,1.4,1); g.add(skull);
  const barBg=new THREE.Mesh(new THREE.BoxGeometry(8,.28,.2),mat('#202833')); barBg.position.set(0,7.6,-.3); g.add(barBg);
  const bar=new THREE.Mesh(new THREE.BoxGeometry(8,.22,.24),mat('#68ff64')); bar.position.set(0,7.6,-.42); bar.name='hpbar'; g.add(bar);
  world.add(g);
  return g;
}
let baseGroup: THREE.Group|null=null;

function makeUi() {
  ui.innerHTML = '';
  ui.insertAdjacentHTML('beforeend', `
    <div id="menuScreen" class="screen">
      <div class="menu-card">
        <div class="logo-mark">🧟</div>
        <h1>ZOMBIE<br>HORDE</h1>
        <div class="subtitle">Multiply the army. Break the defenses. Become the outbreak.</div>
        <button id="playBtn" class="primary">PLAY LEVEL ${save.level}</button>
        <div class="row" style="margin-top:10px">
          <button id="collectionBtn" class="secondary">🧬 Zombie Lab</button>
          <button id="upgradeBtn" class="secondary">⬆ Upgrade Start Count</button>
        </div>
        <div class="small">Desktop: A/D or ←/→ &nbsp; • &nbsp; Mobile: drag left / right</div>
      </div>
    </div>
    <div id="hud" class="hud" style="display:none">
      <div class="top">
        <div class="pill level"><span>LEVEL ${currentLevel.id}</span><span style="color:#91a3bb">•</span><span>${currentLevel.name}</span></div>
        <div class="progress-wrap pill"><strong id="objective">BREAK THE BASE</strong><div class="progress-track"><div id="progress" class="progress-bar"></div></div></div>
        <div class="pill count">🧟 <span id="count">0</span></div>
      </div>
      <div id="toast" class="toast"></div>
      <div class="bottom">
        <div class="controls">
          <button id="labBtn" class="ability"><strong>🧬 ZOMBIE LAB</strong><span>choose army</span></button>
          <button id="mutateBtn" class="ability"><strong>☣ MUTATION</strong><span id="mutationText">READY</span></button>
          <button id="pauseBtn" class="ability"><strong>Ⅱ PAUSE</strong><span>menu</span></button>
        </div>
      </div>
    </div>
    <div id="overlay"></div>
  `);
  document.getElementById('playBtn')!.addEventListener('click',()=>startLevel());
  document.getElementById('collectionBtn')!.addEventListener('click',()=>showCollection(false));
  document.getElementById('upgradeBtn')!.addEventListener('click',()=>{
    const cost=250+save.startBonus*125;
    if(save.coins>=cost){save.coins-=cost;save.startBonus++;saveGame();notify('START COUNT +1');}
    else notify('NOT ENOUGH COINS','#ffb347');
  });
  document.getElementById('labBtn')!.addEventListener('click',()=>showCollection(true));
  document.getElementById('mutateBtn')!.addEventListener('click',()=>chooseMutation());
  document.getElementById('pauseBtn')!.addEventListener('click',()=>pauseToMenu());
}
makeUi();

function setHud(on:boolean){
  (document.getElementById('menuScreen') as HTMLElement).style.display=on?'none':'grid';
  (document.getElementById('hud') as HTMLElement).style.display=on?'block':'none';
}
function updateHud(){
  document.getElementById('count')!.textContent=Math.max(0,Math.floor(hordeCount)).toLocaleString();
  document.getElementById('progress')!.style.width = Math.min(100,(hordeZ/124)*100)+'%';
}
function notify(message:string,color='#d8ff74'){
  const t=document.getElementById('toast') as HTMLElement; t.textContent=message; t.style.color=color; t.classList.add('show');
  window.setTimeout(()=>t.classList.remove('show'),800);
}
function showCollection(fromGame:boolean){
  const overlay=document.getElementById('overlay')!;
  const names:Record<ZombieType,[string,string,string]> = {
    walker:['WALKER','🧟','Balanced starter'],
    runner:['RUNNER','🏃','Fast horde'],
    tank:['TANK','💪','Heavy hitter']
  };
  overlay.innerHTML=`
    <div class="screen">
      <div class="menu-card">
        <div style="font-size:13px;color:#91a3bb;font-weight:800;letter-spacing:1.2px">ZOMBIE LAB</div>
        <h2 style="font-size:32px;margin:7px 0 3px">Build Your Horde</h2>
        <div class="subtitle" style="margin-bottom:4px">Different armies change how the run feels.</div>
        <div class="cards">
          ${Object.entries(names).map(([key,val])=>`
            <button class="card ${save.selected===key?'selected':''}" data-z="${key}">
              <span class="emoji">${val[1]}</span>
              <span class="name">${val[0]}</span>
              <span class="meta">${val[2]}</span>
            </button>`).join('')}
        </div>
        <div class="row"><button id="closeLab" class="secondary">${fromGame?'BACK TO RUN':'BACK'}</button></div>
      </div>
    </div>`;
  overlay.querySelectorAll<HTMLButtonElement>('[data-z]').forEach(btn=>btn.onclick=()=>{
    save.selected=btn.dataset.z as ZombieType; saveGame(); showCollection(fromGame);
  });
  overlay.querySelector('#closeLab')!.addEventListener('click',()=>{overlay.innerHTML='';});
}
function pauseToMenu(){
  runState='menu'; setHud(false); document.getElementById('overlay')!.innerHTML=''; updateHud();
}
function chooseMutation(){
  if(runState!=='playing') return;
  const choices=[['HORDE SURGE','Start each gate phase with +10 zombies.'],['IRON SKIN','Reduce hazard losses by 25%.'],['RABID','Run speed +15%.']];
  const overlay=document.getElementById('overlay')!;
  overlay.innerHTML=`
  <div class="screen"><div class="menu-card">
    <div style="font-size:13px;color:#91a3bb;font-weight:900;letter-spacing:1px">CHOOSE MUTATION</div>
    <h2 style="font-size:34px;margin:8px 0">EVOLVE</h2>
    <div class="cards">${choices.map((c,i)=>`<button class="card" data-m="${i}"><span class="emoji">${['⚡','🛡️','💨'][i]}</span><span class="name">${c[0]}</span><span class="meta">${c[1]}</span></button>`).join('')}</div>
  </div></div>`;
  overlay.querySelectorAll<HTMLButtonElement>('[data-m]').forEach(btn=>btn.onclick=()=>{
    const i=Number(btn.dataset.m); localStorage.setItem('zombie-horde-mutation',String(i)); overlay.innerHTML=''; notify(choices[i][0]);
  });
}

function laneFromX(x:number){ return x<-2.6?-1:(x>2.6?1:0); }

function startLevel(){
  audio();
  currentLevel=LEVELS[Math.min(save.level-1, LEVELS.length-1)];
  buildRun();
  setHud(true);
  runState='playing';
}
function buildRun(){
  world.clear();
  buildWorld();
  for (const t of ['walker','runner','tank'] as ZombieType[]) world.add(zombieMeshes[t]);
  world.add(hordeGroup);
  hordeZ=0; playerX=0; solvedGates=0; solvedHazards=0; solvedSquads=0; attackTimer=0; shake=0;
  baseHp=currentLevel.baseHp; baseMax=currentLevel.baseHp;
  hordeCount=currentLevel.starting+save.startBonus;
  const mult = save.selected==='runner'?1.10:(save.selected==='tank'?.9:1);
  currentLevel.gates.forEach(g=>gates.push(createGate(g.z,g.left,g.right)));
  currentLevel.hazards.forEach(h=>createHazard(h.z,h.lane,h.label));
  currentLevel.squads.forEach(s=>createSquad(s.z,s.lane));
  baseGroup=createBase(baseHp);
  if (mult!==1) notify(save.selected==='runner'?'RUNNER SPEED!':'TANK POWER!');
  updateHud();
}

function applyGate(effect:GateEffect){
  const before=hordeCount;
  if(effect.multiplier) hordeCount=Math.floor(hordeCount*effect.multiplier);
  if(effect.additive) hordeCount=Math.max(1,hordeCount+effect.additive);
  const delta=Math.floor(hordeCount-before);
  notify((effect.label)+'   '+(delta>=0?'+':'' )+delta,delta>=0?'#d8ff74':'#ff7878');
  audio(delta>=0?660:240);
}
function applyHazard(amount:number,label:string){
  const reduction=localStorage.getItem('zombie-horde-mutation')==='1'?.75:1;
  const lost=Math.max(1,Math.floor(amount*reduction));
  hordeCount=Math.max(1,hordeCount-lost);
  notify(label+'  -'+lost,'#ff8e78'); audio(180);
}
function applySquad(amount:number){
  const power = save.selected==='tank'?0.75:1;
  const lost=Math.max(1,Math.floor(amount*power));
  hordeCount=Math.max(1,hordeCount-lost);
  notify('DEFENSE  -'+lost,'#ff8e78'); audio(160);
}

function updateHorde(){
  const selected=save.selected;
  const mesh=zombieMeshes[selected];
  for(const t of ['walker','runner','tank'] as ZombieType[]) zombieMeshes[t].count=0;
  mesh.count=Math.min(Math.floor(hordeCount),600);
  const dummy=new THREE.Object3D();
  const rows=Math.ceil(mesh.count/10);
  for(let i=0;i<mesh.count;i++){
    const row=Math.floor(i/10), col=i%10;
    const tx=(col-4.5)*.78 + Math.sin(i*2.17)*.09;
    const tz=(rows-row)*.6 - 1.8 + Math.cos(i*1.8)*.08;
    const bob=Math.sin(performance.now()/125 + i*.42)*.035;
    dummy.position.set(playerX+tx,bob+.72,hordeZ+tz);
    dummy.rotation.set(0,Math.sin(i*3.1)*.08,0);
    const scale=selected==='tank'?1.25:(selected==='runner'?.86:1);
    dummy.scale.setScalar(scale);
    dummy.updateMatrix();
    mesh.setMatrixAt(i,dummy.matrix);
  }
  mesh.instanceMatrix.needsUpdate=true;
  hordeAura.position.set(playerX,hordeZ-.7,.03);
  hordeAura.scale.setScalar(Math.min(1.9,1+hordeCount/170));
}

function handleCrossings(){
  while(solvedGates<currentLevel.gates.length && hordeZ>=currentLevel.gates[solvedGates].z){
    const gate=currentLevel.gates[solvedGates];
    const effect=playerX<0?gate.left:gate.right;
    applyGate(effect); solvedGates++;
  }
  while(solvedHazards<currentLevel.hazards.length && hordeZ>=currentLevel.hazards[solvedHazards].z){
    const h=currentLevel.hazards[solvedHazards];
    if(Math.abs(laneFromX(playerX)-h.lane)<1) applyHazard(h.amount,h.label);
    solvedHazards++;
  }
  while(solvedSquads<currentLevel.squads.length && hordeZ>=currentLevel.squads[solvedSquads].z){
    const s=currentLevel.squads[solvedSquads];
    if(Math.abs(laneFromX(playerX)-s.lane)<1) applySquad(s.amount);
    solvedSquads++;
  }
}

function beginAttack(){
  runState='attacking'; attackTimer=0;
}
function updateAttack(dt:number){
  attackTimer+=dt;
  const damageRate=(save.selected==='tank'?1.4:save.selected==='runner'?.95:1)*Math.max(1,hordeCount/12);
  baseHp=Math.max(0,baseHp-damageRate*dt*12);
  if(baseGroup){
    baseGroup.scale.y=1+Math.sin(attackTimer*22)*.025;
    const bar=baseGroup.getObjectByName('hpbar') as THREE.Mesh|undefined;
    if(bar){ bar.scale.x=Math.max(.01,baseHp/baseMax); bar.position.x=-4*(1-bar.scale.x); }
    baseGroup.position.x=Math.sin(attackTimer*34)*.04;
    if(baseHp<=0 || attackTimer>4.2) finishWin();
  }
}
function finishWin(){
  runState='won';
  const reward=Math.floor(80+currentLevel.id*35+hordeCount*.8);
  save.coins+=reward;
  if(save.level<LEVELS.length) save.level++;
  saveGame();
  audio(880); audio(1100);
  const overlay=document.getElementById('overlay')!;
  overlay.innerHTML=`
    <div class="screen"><div class="menu-card">
      <div style="font-size:54px">💥</div>
      <div style="font-size:13px;color:#91a3bb;font-weight:900;letter-spacing:1px">ENEMY BASE DESTROYED</div>
      <h2 style="font-size:42px;margin:6px 0">HORDE WINS</h2>
      <div class="reward">🧟 ${Math.floor(hordeCount).toLocaleString()} zombies survived<br>🪙 +${reward} coins</div>
      <button id="nextBtn" class="primary">${currentLevel.id<LEVELS.length?'NEXT LEVEL':'RESTART CAMPAIGN'}</button>
      <div class="small">Total coins: ${save.coins.toLocaleString()}</div>
    </div></div>`;
  overlay.querySelector('#nextBtn')!.addEventListener('click',()=>{
    if(save.level>LEVELS.length) save.level=1;
    overlay.innerHTML=''; startLevel();
  });
}
function finishLose(){
  runState='lost';
  const overlay=document.getElementById('overlay')!;
  overlay.innerHTML=`
    <div class="screen"><div class="menu-card">
      <div style="font-size:50px">💀</div>
      <h2 style="font-size:40px;margin:6px 0">HORDE STOPPED</h2>
      <div class="reward">The defenses broke your army.</div>
      <button id="retryBtn" class="primary">RETRY</button>
      <div class="row" style="margin-top:10px"><button id="backBtn" class="secondary">MAIN MENU</button></div>
    </div></div>`;
  overlay.querySelector('#retryBtn')!.addEventListener('click',()=>{overlay.innerHTML='';startLevel();});
  overlay.querySelector('#backBtn')!.addEventListener('click',()=>{overlay.innerHTML='';pauseToMenu();});
}

function audio(freq=520){
  try{
    const C=new AudioContext();
    const o=C.createOscillator(); const g=C.createGain();
    o.type='triangle'; o.frequency.value=freq; g.gain.value=.0001;
    o.connect(g); g.connect(C.destination); const now=C.currentTime;
    g.gain.exponentialRampToValueAtTime(.06,now+.01); g.gain.exponentialRampToValueAtTime(.0001,now+.11);
    o.start(now); o.stop(now+.12);
  }catch{}
}

function pointerX(clientX:number){
  const rect=renderer.domElement.getBoundingClientRect();
  const n=(clientX-rect.left)/rect.width;
  playerX=THREE.MathUtils.lerp(-6.8,6.8,THREE.MathUtils.clamp(n,0,1));
}
let drag=false;
renderer.domElement.addEventListener('pointerdown',e=>{drag=true;pointerX(e.clientX);renderer.domElement.setPointerCapture(e.pointerId);});
renderer.domElement.addEventListener('pointermove',e=>{if(drag)pointerX(e.clientX);});
renderer.domElement.addEventListener('pointerup',()=>drag=false);
addEventListener('keydown',e=>{
  if(runState!=='playing') return;
  if(e.key==='a'||e.key==='ArrowLeft') playerX-=1.1;
  if(e.key==='d'||e.key==='ArrowRight') playerX+=1.1;
  playerX=THREE.MathUtils.clamp(playerX,-6.8,6.8);
});

const keys=new Set<string>();
addEventListener('keydown',e=>keys.add(e.key));
addEventListener('keyup',e=>keys.delete(e.key));

function animate(now:number){
  requestAnimationFrame(animate);
  const dt=Math.min(.033,(now-lastTime)/1000); lastTime=now;

  if(runState==='playing'){
    if(keys.has('a')||keys.has('ArrowLeft')) playerX-=dt*8;
    if(keys.has('d')||keys.has('ArrowRight')) playerX+=dt*8;
    playerX=THREE.MathUtils.clamp(playerX,-6.8,6.8);
    const speedBoost=save.selected==='runner'?1.12:(localStorage.getItem('zombie-horde-mutation')==='2'?1.15:1);
    hordeZ+=currentLevel.speed*speedBoost*dt;
    handleCrossings();
    if(hordeZ>=118) beginAttack();
  } else if(runState==='attacking') updateAttack(dt);

  updateHorde();
  const targetZ=hordeZ+18;
  camera.position.x=THREE.MathUtils.lerp(camera.position.x,playerX*.34,dt*6);
  camera.position.z=THREE.MathUtils.lerp(camera.position.z,hordeZ-22,dt*4);
  camera.lookAt(playerX*.12,2.1,targetZ);
  if(shake>0){shake=Math.max(0,shake-dt);camera.position.x+=(Math.random()-.5)*shake;camera.position.y+=(Math.random()-.5)*shake;}

  updateHud();
  renderer.render(scene,camera);
}
requestAnimationFrame(animate);
addEventListener('resize',()=>{
  camera.aspect=innerWidth/innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth,innerHeight);
});
