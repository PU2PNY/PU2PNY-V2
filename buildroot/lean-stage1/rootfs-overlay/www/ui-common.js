/* PU2PNY-V2 shared panel runtime.
   Provides the window.PNY helpers, theme, top navigation, the auto-closing
   operation overlay, the connected/disconnected watches, and the rule that
   hides any box with no real data. Vanilla JS, no dependencies. Mirrors the
   conventions of the shipping ui-common.js so pages wire to the same contract.

   On the device the Go daemon serves these files at clean routes (/dashboard,
   /internet, …). For local preview the nav links use the .html file names, and
   the daemon maps each route to its file. */
(function(){
  var ROUTE={live:'index.html',internet:'internet.html',hotspot:'hotspot.html',direct:'direct.html',
    aprs:'aprs.html',history:'history.html',display:'display.html',system:'system.html',expert:'expert.html'};
  function q(id){return document.getElementById(id)}
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function locale(){var l=localStorage.getItem('pu2pny-language')||'pt';return l==='en'?'en-US':l==='es'?'es-ES':'pt-BR'}
  function fmtTime(v){if(!v)return'—';try{return new Date(v).toLocaleString(locale())}catch(e){return String(v)}}
  function formatNumber(v,o){try{return new Intl.NumberFormat(locale(),o||{}).format(v)}catch(e){return String(v)}}
  /* Flags are served by the device daemon at /flags/4x3/<cc>.svg; the panel
     ships none. Images that 404 (e.g. local file preview) remove themselves. */
  function flagUrl(code){var cc=String(code||'').toLowerCase();return /^[a-z]{2}$/.test(cc)?'/flags/4x3/'+cc+'.svg':''}

  /* The operation overlay: a non-GET request shows it automatically, and it
     AUTO-CLOSES on success — a status notice never gets stuck on screen. */
  function operation(title,message){
    var old=q('pnyOp');if(old)old.remove();
    var ov=document.createElement('div');ov.id='pnyOp';
    ov.style.cssText='position:fixed;inset:0;z-index:5000;background:rgba(2,8,14,.62);display:grid;place-items:center;padding:18px';
    var box=document.createElement('div');box.style.cssText='width:min(540px,100%);background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:var(--shadow)';
    box.innerHTML='<h2 style="margin-top:0">'+esc(title||'Executando')+'</h2><div style="height:6px;background:var(--card2);border-radius:999px;overflow:hidden"><i id="pnyOpBar" style="display:block;width:35%;height:100%;background:var(--blue);animation:pnyop 1.2s ease-in-out infinite alternate"></i></div><p id="pnyOpMsg" style="margin-bottom:0">'+esc(message||'Aguarde…')+'</p><button class="btn hidden" id="pnyOpClose" style="margin-top:14px">Fechar</button>';
    if(!q('pnyOpKeyframes')){var kf=document.createElement('style');kf.id='pnyOpKeyframes';kf.textContent='@keyframes pnyop{from{transform:translateX(-80%)}to{transform:translateX(220%)}}';document.head.appendChild(kf)}
    ov.appendChild(box);document.body.appendChild(ov);
    function set(state,msg){var m=q('pnyOpMsg'),bar=q('pnyOpBar'),close=q('pnyOpClose');if(m&&msg!=null)m.textContent=msg;
      if(state==='done'||state==='error'){if(bar){bar.style.animation='none';bar.style.width='100%';bar.style.transform='none';bar.style.background=state==='done'?'var(--green)':'var(--red)'}if(close){close.classList.remove('hidden');close.onclick=function(){ov.remove()}}}}
    return {step:function(m){set('running',m)},
      progress:function(p,m){p=Math.max(0,Math.min(100,Number(p)||0));var bar=q('pnyOpBar');if(bar){bar.style.animation='none';bar.style.transform='none';bar.style.width=p+'%'}set('running',(m||'Executando…')+' · '+Math.round(p)+'%')},
      done:function(m,delay){set('done',m||'Concluído.');setTimeout(function(){if(ov.parentNode)ov.remove()},delay==null?1200:delay)},
      error:function(m){set('error',m||'Não foi possível concluir.')},close:function(){if(ov.parentNode)ov.remove()}};
  }

  async function getj(url,opt,timeout){
    var ctl=window.AbortController?new AbortController():null,timer=null,o=Object.assign({cache:'no-store'},opt||{}),method=String(o.method||'GET').toUpperCase(),auto=null;
    if(method!=='GET'&&!o.pnySilent&&!q('pnyOp'))auto=operation('Aplicando alteração','Enviando, validando e aguardando confirmação do sistema...');
    delete o.pnySilent;
    if(ctl){o.signal=ctl.signal;timer=setTimeout(function(){ctl.abort()},timeout||8000)}
    try{
      var r=await fetch(url,o),j=await r.json().catch(function(){return {}});
      if(!r.ok){var m=j.error||j.message||('HTTP '+r.status);if(/abort/i.test(m))m='A confirmação demorou além do limite do navegador. Consulte o estado atual antes de tentar novamente.';throw new Error(m)}
      if(auto)auto.done(j.message||'Alteração aplicada.');return j;
    }catch(e){var mm=String(e&&e.message||e||'');if(/abort/i.test(mm))e=new Error('A confirmação demorou além do limite do navegador. Consulte o estado atual antes de tentar novamente.');if(auto)auto.error(e.message);throw e}
    finally{if(timer)clearTimeout(timer)}
  }

  function setTheme(t){document.documentElement.setAttribute('data-theme',t);localStorage.setItem('pu2pny-theme',t);var b=q('themeToggle');if(b)b.textContent=t==='dark'?'☀ Claro':'☾ Escuro'}
  function initTheme(){setTheme(localStorage.getItem('pu2pny-theme')||'dark');var b=q('themeToggle');if(b)b.onclick=function(){setTheme(document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark')}}

  function footer(active){
    if(q('pnyFooter'))return;
    var f=document.createElement('footer');f.id='pnyFooter';
    f.style.cssText='margin:28px auto 14px;max-width:1460px;padding:14px 22px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;text-align:center';
    f.textContent='PU2PNY-V2 · versão…';document.body.appendChild(f);
    getj('/api/status').then(function(s){f.textContent='PU2PNY-V2 · '+(s.version||'versão indisponível')}).catch(function(){f.textContent='PU2PNY-V2'});
  }
  function tools(active){
    var tools=document.querySelector('.navtools');if(!tools)return;
    if(!q('language')){var s=document.createElement('select');s.id='language';s.setAttribute('aria-label','Idioma');s.innerHTML='<option value="pt">PT</option><option value="en">EN</option><option value="es">ES</option>';tools.insertBefore(s,tools.firstChild)}
    if(!q('modeToggle')){var b=document.createElement('button');b.className='btn';b.id='modeToggle';tools.appendChild(b)}
    q('modeToggle').textContent=active==='expert'?'Básico':'Expert';
    q('modeToggle').onclick=function(){location.href=active==='expert'?ROUTE.live:ROUTE.expert};
    if(!document.querySelector('script[data-pny-language]')){var sc=document.createElement('script');sc.src='ui-language.js';sc.dataset.pnyLanguage='1';document.body.appendChild(sc)}
    else if(window.translateNavigation)window.translateNavigation();
  }
  function nav(active){
    var items=[['live','Ao Vivo'],['internet','Internet'],['hotspot','Protocolos'],['direct','Direct'],['aprs','APRS'],['history','Histórico'],['display','Display'],['system','Sistema']];
    var n=q('mainNav');if(n)n.innerHTML=items.map(function(x){return '<a '+(x[0]===active?'class="active" ':'')+'href="'+ROUTE[x[0]]+'">'+x[1]+'</a>'}).join('');
    tools(active);footer(active);startClock();startConnectivityWatch();
  }

  /* Clock in the nav, synced to the device UTC so it does not drift. */
  var clockStarted=false,serverUTC=0,syncAt=0,tz='';
  function renderClock(){var l=q('clockLocal');if(!l)return;var ms=serverUTC?serverUTC+(Date.now()-syncAt):Date.now();var d=new Date(ms);try{l.textContent=new Intl.DateTimeFormat(locale(),{timeZone:tz||undefined,hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(d)}catch(e){l.textContent=d.toLocaleTimeString()}}
  async function syncClock(){try{var s=await getj('/api/system',null,4500),utc=Date.parse(s.utc||'');if(Number.isFinite(utc)){serverUTC=utc;syncAt=Date.now()}tz=s.timezone||tz}catch(e){}renderClock()}
  function startClock(){if(clockStarted)return;clockStarted=true;syncClock();setInterval(renderClock,1000);setInterval(function(){if(!document.hidden)syncClock()},60000)}

  /* Internet alert — raised when the uplink is down, cleared when it returns. */
  var connStarted=false,offlineHits=0;
  function startConnectivityWatch(){
    if(connStarted)return;connStarted=true;
    async function check(){if(document.hidden)return;try{var c=await getj('/api/connectivity',null,4000),old=q('pnyNetAlert');
      if(c.internet){offlineHits=0;if(old)old.remove();return}offlineHits++;if(offlineHits<2||old||q('pnyOp'))return;
      var n=document.createElement('div');n.id='pnyNetAlert';n.setAttribute('role','alert');
      n.style.cssText='position:fixed;left:50%;top:70px;transform:translateX(-50%);z-index:4100;width:min(620px,calc(100vw - 28px));padding:13px 15px;border:1px solid var(--red);border-radius:14px;background:var(--card);box-shadow:var(--shadow)';
      n.innerHTML='<b>Internet desconectada</b><div class="muted" style="margin-top:4px">Verifique o cabo ou as redes Wi‑Fi salvas. O painel local continua disponível.</div>';
      document.body.appendChild(n)}catch(_){}}
    setTimeout(check,3500);setInterval(check,10000);document.addEventListener('visibilitychange',function(){if(!document.hidden)check()});
  }

  /* Hide any box whose only value is empty or a placeholder — the permanent
     rule that boxes with no data must not be shown. */
  function realValue(v){v=String(v==null?'':v).trim().toLowerCase();return !!v&&v!=='—'&&v!=='--'&&v!=='indisponível'&&v!=='unavailable'&&v!=='no disponible'&&v!=='não verificado'}
  function realOnly(id,show){var el=typeof id==='string'?q(id):id;if(!el)return;var target=el.closest('[data-real-only],.row,.metric,.fact,.pny-healthitem')||el;var yes=show==null?realValue(el.textContent):!!show;target.classList.toggle('hidden',!yes)}
  function sweepRealOnly(root){(root||document).querySelectorAll('[data-real-only],.facts>.fact,.metrics>.metric,.rows>.row,.pny-healthitem').forEach(function(n){if(n.hasAttribute('data-real-keep'))return;var v=n.querySelector('b,code,[data-real-value]')||n;realOnly(v)})}
  var realObserver=null;
  function observeRealOnly(){sweepRealOnly(document);if(realObserver||!window.MutationObserver)return;var pending=false;realObserver=new MutationObserver(function(){if(pending)return;pending=true;requestAnimationFrame(function(){pending=false;sweepRealOnly(document)})});realObserver.observe(document.body,{subtree:true,childList:true,characterData:true})}

  window.PNY={q:q,esc:esc,getj:getj,setTheme:setTheme,initTheme:initTheme,flagUrl:flagUrl,fmtTime:fmtTime,locale:locale,formatNumber:formatNumber,nav:nav,startClock:startClock,operation:operation,realOnly:realOnly,sweepRealOnly:sweepRealOnly,observeRealOnly:observeRealOnly,ROUTE:ROUTE};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',observeRealOnly);else observeRealOnly();
})();
