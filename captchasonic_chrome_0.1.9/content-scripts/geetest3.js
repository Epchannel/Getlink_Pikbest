var geetest3=function(){"use strict";function Pe(e){return e}const V={equals:(e,s)=>e===s};let ie=Y;const v=1,S=2;var T=null;let B=null,ae=null,u=null,h=null,w=null,k=0;function G(e,s){s=s?Object.assign({},V,s):V;const r={value:e,observers:null,observerSlots:null,comparator:s.equals||void 0},t=i=>(typeof i=="function"&&(i=i(r.value)),H(r,i));return[le.bind(r),t]}function oe(e){if(u===null)return e();const s=u;u=null;try{return e()}finally{u=s}}function le(){if(this.sources&&this.state)if(this.state===v)z(this);else{const e=h;h=null,C(()=>P(this)),h=e}if(u){const e=this.observers?this.observers.length:0;u.sources?(u.sources.push(this),u.sourceSlots.push(e)):(u.sources=[this],u.sourceSlots=[e]),this.observers?(this.observers.push(u),this.observerSlots.push(u.sources.length-1)):(this.observers=[u],this.observerSlots=[u.sources.length-1])}return this.value}function H(e,s,r){let t=e.value;return(!e.comparator||!e.comparator(t,s))&&(e.value=s,e.observers&&e.observers.length&&C(()=>{for(let i=0;i<e.observers.length;i+=1){const g=e.observers[i],A=B&&B.running;A&&B.disposed.has(g),(A?!g.tState:!g.state)&&(g.pure?h.push(g):w.push(g),g.observers&&J(g)),A||(g.state=v)}if(h.length>1e6)throw h=[],new Error})),s}function z(e){if(!e.fn)return;_(e);const s=k;ge(e,e.value,s)}function ge(e,s,r){let t;const i=T,g=u;u=T=e;try{t=e.fn(s)}catch(A){return e.pure&&(e.state=v,e.owned&&e.owned.forEach(_),e.owned=null),e.updatedAt=r+1,Q(A)}finally{u=g,T=i}(!e.updatedAt||e.updatedAt<=r)&&(e.updatedAt!=null&&"observers"in e?H(e,t):e.value=t,e.updatedAt=r)}function Z(e){if(e.state===0)return;if(e.state===S)return P(e);if(e.suspense&&oe(e.suspense.inFallback))return e.suspense.effects.push(e);const s=[e];for(;(e=e.owner)&&(!e.updatedAt||e.updatedAt<k);)e.state&&s.push(e);for(let r=s.length-1;r>=0;r--)if(e=s[r],e.state===v)z(e);else if(e.state===S){const t=h;h=null,C(()=>P(e,s[0])),h=t}}function C(e,s){if(h)return e();let r=!1;h=[],w?r=!0:w=[],k++;try{const t=e();return ce(r),t}catch(t){r||(w=null),h=null,Q(t)}}function ce(e){if(h&&(Y(h),h=null),e)return;const s=w;w=null,s.length&&C(()=>ie(s))}function Y(e){for(let s=0;s<e.length;s++)Z(e[s])}function P(e,s){e.state=0;for(let r=0;r<e.sources.length;r+=1){const t=e.sources[r];if(t.sources){const i=t.state;i===v?t!==s&&(!t.updatedAt||t.updatedAt<k)&&Z(t):i===S&&P(t,s)}}}function J(e){for(let s=0;s<e.observers.length;s+=1){const r=e.observers[s];r.state||(r.state=S,r.pure?h.push(r):w.push(r),r.observers&&J(r))}}function _(e){let s;if(e.sources)for(;e.sources.length;){const r=e.sources.pop(),t=e.sourceSlots.pop(),i=r.observers;if(i&&i.length){const g=i.pop(),A=r.observerSlots.pop();t<i.length&&(g.sourceSlots[A]=t,i[t]=g,r.observerSlots[t]=A)}}if(e.tOwned){for(s=e.tOwned.length-1;s>=0;s--)_(e.tOwned[s]);delete e.tOwned}if(e.owned){for(s=e.owned.length-1;s>=0;s--)_(e.owned[s]);e.owned=null}if(e.cleanups){for(s=e.cleanups.length-1;s>=0;s--)e.cleanups[s]();e.cleanups=null}e.state=0}function me(e){return e instanceof Error?e:new Error(typeof e=="string"?e:"Unknown error",{cause:e})}function Q(e,s=T){throw me(e)}async function ue(e,s,r){if(!e()||e().ACTIVE===!1||e().OPTIONS[r].ENABLED===!1)return!1;function t(A,L){try{return L.includes(A)}catch(R){return console.error("Error parsing URLs:",R),!1}}const i=e().BLACKLIST;return!(t(s(),i)&&e().BLACKLISTENABLED)}const Ae={matches:["<all_urls>"],allFrames:!0,match_about_blank:!1,async main(){const[e]=G(window.location.host),[s,r]=G(await chrome.storage.local.get("settings"));r(s().settings),await ue(s,e,"GEETEST")&&(async()=>window.geetestV3Injected||(window.geetestV3Injected=!0))()}};function fe(e){return e&&e.__esModule&&Object.prototype.hasOwnProperty.call(e,"default")?e.default:e}var M={exports:{}},he=M.exports,X;function xe(){return X||(X=1,function(e,s){(function(r,t){t(e)})(typeof globalThis<"u"?globalThis:typeof self<"u"?self:he,function(r){if(!(globalThis.chrome&&globalThis.chrome.runtime&&globalThis.chrome.runtime.id))throw new Error("This script should only be loaded in a browser extension.");if(globalThis.browser&&globalThis.browser.runtime&&globalThis.browser.runtime.id)r.exports=globalThis.browser;else{const t="The message port closed before a response was received.",i=g=>{const A={alarms:{clear:{minArgs:0,maxArgs:1},clearAll:{minArgs:0,maxArgs:0},get:{minArgs:0,maxArgs:1},getAll:{minArgs:0,maxArgs:0}},bookmarks:{create:{minArgs:1,maxArgs:1},get:{minArgs:1,maxArgs:1},getChildren:{minArgs:1,maxArgs:1},getRecent:{minArgs:1,maxArgs:1},getSubTree:{minArgs:1,maxArgs:1},getTree:{minArgs:0,maxArgs:0},move:{minArgs:2,maxArgs:2},remove:{minArgs:1,maxArgs:1},removeTree:{minArgs:1,maxArgs:1},search:{minArgs:1,maxArgs:1},update:{minArgs:2,maxArgs:2}},browserAction:{disable:{minArgs:0,maxArgs:1,fallbackToNoCallback:!0},enable:{minArgs:0,maxArgs:1,fallbackToNoCallback:!0},getBadgeBackgroundColor:{minArgs:1,maxArgs:1},getBadgeText:{minArgs:1,maxArgs:1},getPopup:{minArgs:1,maxArgs:1},getTitle:{minArgs:1,maxArgs:1},openPopup:{minArgs:0,maxArgs:0},setBadgeBackgroundColor:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0},setBadgeText:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0},setIcon:{minArgs:1,maxArgs:1},setPopup:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0},setTitle:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0}},browsingData:{remove:{minArgs:2,maxArgs:2},removeCache:{minArgs:1,maxArgs:1},removeCookies:{minArgs:1,maxArgs:1},removeDownloads:{minArgs:1,maxArgs:1},removeFormData:{minArgs:1,maxArgs:1},removeHistory:{minArgs:1,maxArgs:1},removeLocalStorage:{minArgs:1,maxArgs:1},removePasswords:{minArgs:1,maxArgs:1},removePluginData:{minArgs:1,maxArgs:1},settings:{minArgs:0,maxArgs:0}},commands:{getAll:{minArgs:0,maxArgs:0}},contextMenus:{remove:{minArgs:1,maxArgs:1},removeAll:{minArgs:0,maxArgs:0},update:{minArgs:2,maxArgs:2}},cookies:{get:{minArgs:1,maxArgs:1},getAll:{minArgs:1,maxArgs:1},getAllCookieStores:{minArgs:0,maxArgs:0},remove:{minArgs:1,maxArgs:1},set:{minArgs:1,maxArgs:1}},devtools:{inspectedWindow:{eval:{minArgs:1,maxArgs:2,singleCallbackArg:!1}},panels:{create:{minArgs:3,maxArgs:3,singleCallbackArg:!0},elements:{createSidebarPane:{minArgs:1,maxArgs:1}}}},downloads:{cancel:{minArgs:1,maxArgs:1},download:{minArgs:1,maxArgs:1},erase:{minArgs:1,maxArgs:1},getFileIcon:{minArgs:1,maxArgs:2},open:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0},pause:{minArgs:1,maxArgs:1},removeFile:{minArgs:1,maxArgs:1},resume:{minArgs:1,maxArgs:1},search:{minArgs:1,maxArgs:1},show:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0}},extension:{isAllowedFileSchemeAccess:{minArgs:0,maxArgs:0},isAllowedIncognitoAccess:{minArgs:0,maxArgs:0}},history:{addUrl:{minArgs:1,maxArgs:1},deleteAll:{minArgs:0,maxArgs:0},deleteRange:{minArgs:1,maxArgs:1},deleteUrl:{minArgs:1,maxArgs:1},getVisits:{minArgs:1,maxArgs:1},search:{minArgs:1,maxArgs:1}},i18n:{detectLanguage:{minArgs:1,maxArgs:1},getAcceptLanguages:{minArgs:0,maxArgs:0}},identity:{launchWebAuthFlow:{minArgs:1,maxArgs:1}},idle:{queryState:{minArgs:1,maxArgs:1}},management:{get:{minArgs:1,maxArgs:1},getAll:{minArgs:0,maxArgs:0},getSelf:{minArgs:0,maxArgs:0},setEnabled:{minArgs:2,maxArgs:2},uninstallSelf:{minArgs:0,maxArgs:1}},notifications:{clear:{minArgs:1,maxArgs:1},create:{minArgs:1,maxArgs:2},getAll:{minArgs:0,maxArgs:0},getPermissionLevel:{minArgs:0,maxArgs:0},update:{minArgs:2,maxArgs:2}},pageAction:{getPopup:{minArgs:1,maxArgs:1},getTitle:{minArgs:1,maxArgs:1},hide:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0},setIcon:{minArgs:1,maxArgs:1},setPopup:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0},setTitle:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0},show:{minArgs:1,maxArgs:1,fallbackToNoCallback:!0}},permissions:{contains:{minArgs:1,maxArgs:1},getAll:{minArgs:0,maxArgs:0},remove:{minArgs:1,maxArgs:1},request:{minArgs:1,maxArgs:1}},runtime:{getBackgroundPage:{minArgs:0,maxArgs:0},getPlatformInfo:{minArgs:0,maxArgs:0},openOptionsPage:{minArgs:0,maxArgs:0},requestUpdateCheck:{minArgs:0,maxArgs:0},sendMessage:{minArgs:1,maxArgs:3},sendNativeMessage:{minArgs:2,maxArgs:2},setUninstallURL:{minArgs:1,maxArgs:1}},sessions:{getDevices:{minArgs:0,maxArgs:1},getRecentlyClosed:{minArgs:0,maxArgs:1},restore:{minArgs:0,maxArgs:1}},storage:{local:{clear:{minArgs:0,maxArgs:0},get:{minArgs:0,maxArgs:1},getBytesInUse:{minArgs:0,maxArgs:1},remove:{minArgs:1,maxArgs:1},set:{minArgs:1,maxArgs:1}},managed:{get:{minArgs:0,maxArgs:1},getBytesInUse:{minArgs:0,maxArgs:1}},sync:{clear:{minArgs:0,maxArgs:0},get:{minArgs:0,maxArgs:1},getBytesInUse:{minArgs:0,maxArgs:1},remove:{minArgs:1,maxArgs:1},set:{minArgs:1,maxArgs:1}}},tabs:{captureVisibleTab:{minArgs:0,maxArgs:2},create:{minArgs:1,maxArgs:1},detectLanguage:{minArgs:0,maxArgs:1},discard:{minArgs:0,maxArgs:1},duplicate:{minArgs:1,maxArgs:1},executeScript:{minArgs:1,maxArgs:2},get:{minArgs:1,maxArgs:1},getCurrent:{minArgs:0,maxArgs:0},getZoom:{minArgs:0,maxArgs:1},getZoomSettings:{minArgs:0,maxArgs:1},goBack:{minArgs:0,maxArgs:1},goForward:{minArgs:0,maxArgs:1},highlight:{minArgs:1,maxArgs:1},insertCSS:{minArgs:1,maxArgs:2},move:{minArgs:2,maxArgs:2},query:{minArgs:1,maxArgs:1},reload:{minArgs:0,maxArgs:2},remove:{minArgs:1,maxArgs:1},removeCSS:{minArgs:1,maxArgs:2},sendMessage:{minArgs:2,maxArgs:3},setZoom:{minArgs:1,maxArgs:2},setZoomSettings:{minArgs:1,maxArgs:2},update:{minArgs:1,maxArgs:2}},topSites:{get:{minArgs:0,maxArgs:0}},webNavigation:{getAllFrames:{minArgs:1,maxArgs:1},getFrame:{minArgs:1,maxArgs:1}},webRequest:{handlerBehaviorChanged:{minArgs:0,maxArgs:0}},windows:{create:{minArgs:0,maxArgs:1},get:{minArgs:1,maxArgs:2},getAll:{minArgs:0,maxArgs:1},getCurrent:{minArgs:0,maxArgs:1},getLastFocused:{minArgs:0,maxArgs:1},remove:{minArgs:1,maxArgs:1},update:{minArgs:2,maxArgs:2}}};if(Object.keys(A).length===0)throw new Error("api-metadata.json has not been included in browser-polyfill");class L extends WeakMap{constructor(a,l=void 0){super(l),this.createItem=a}get(a){return this.has(a)||this.set(a,this.createItem(a)),super.get(a)}}const R=n=>n&&typeof n=="object"&&typeof n.then=="function",se=(n,a)=>(...l)=>{g.runtime.lastError?n.reject(new Error(g.runtime.lastError.message)):a.singleCallbackArg||l.length<=1&&a.singleCallbackArg!==!1?n.resolve(l[0]):n.resolve(l)},K=n=>n==1?"argument":"arguments",Se=(n,a)=>function(c,...f){if(f.length<a.minArgs)throw new Error(`Expected at least ${a.minArgs} ${K(a.minArgs)} for ${n}(), got ${f.length}`);if(f.length>a.maxArgs)throw new Error(`Expected at most ${a.maxArgs} ${K(a.maxArgs)} for ${n}(), got ${f.length}`);return new Promise((x,d)=>{if(a.fallbackToNoCallback)try{c[n](...f,se({resolve:x,reject:d},a))}catch(o){console.warn(`${n} API method doesn't seem to support the callback parameter, falling back to call it without a callback: `,o),c[n](...f),a.fallbackToNoCallback=!1,a.noCallback=!0,x()}else a.noCallback?(c[n](...f),x()):c[n](...f,se({resolve:x,reject:d},a))})},re=(n,a,l)=>new Proxy(a,{apply(c,f,x){return l.call(f,n,...x)}});let O=Function.call.bind(Object.prototype.hasOwnProperty);const $=(n,a={},l={})=>{let c=Object.create(null),f={has(d,o){return o in n||o in c},get(d,o,p){if(o in c)return c[o];if(!(o in n))return;let m=n[o];if(typeof m=="function")if(typeof a[o]=="function")m=re(n,n[o],a[o]);else if(O(l,o)){let y=Se(o,l[o]);m=re(n,n[o],y)}else m=m.bind(n);else if(typeof m=="object"&&m!==null&&(O(a,o)||O(l,o)))m=$(m,a[o],l[o]);else if(O(l,"*"))m=$(m,a[o],l["*"]);else return Object.defineProperty(c,o,{configurable:!0,enumerable:!0,get(){return n[o]},set(y){n[o]=y}}),m;return c[o]=m,m},set(d,o,p,m){return o in c?c[o]=p:n[o]=p,!0},defineProperty(d,o,p){return Reflect.defineProperty(c,o,p)},deleteProperty(d,o){return Reflect.deleteProperty(c,o)}},x=Object.create(n);return new Proxy(x,f)},q=n=>({addListener(a,l,...c){a.addListener(n.get(l),...c)},hasListener(a,l){return a.hasListener(n.get(l))},removeListener(a,l){a.removeListener(n.get(l))}}),Te=new L(n=>typeof n!="function"?n:function(l){const c=$(l,{},{getContent:{minArgs:0,maxArgs:0}});n(c)}),te=new L(n=>typeof n!="function"?n:function(l,c,f){let x=!1,d,o=new Promise(E=>{d=function(b){x=!0,E(b)}}),p;try{p=n(l,c,d)}catch(E){p=Promise.reject(E)}const m=p!==!0&&R(p);if(p!==!0&&!m&&!x)return!1;const y=E=>{E.then(b=>{f(b)},b=>{let W;b&&(b instanceof Error||typeof b.message=="string")?W=b.message:W="An unexpected error occurred",f({__mozWebExtensionPolyfillReject__:!0,message:W})}).catch(b=>{console.error("Failed to send onMessage rejected reply",b)})};return y(m?p:o),!0}),ke=({reject:n,resolve:a},l)=>{g.runtime.lastError?g.runtime.lastError.message===t?a():n(new Error(g.runtime.lastError.message)):l&&l.__mozWebExtensionPolyfillReject__?n(new Error(l.message)):a(l)},ne=(n,a,l,...c)=>{if(c.length<a.minArgs)throw new Error(`Expected at least ${a.minArgs} ${K(a.minArgs)} for ${n}(), got ${c.length}`);if(c.length>a.maxArgs)throw new Error(`Expected at most ${a.maxArgs} ${K(a.maxArgs)} for ${n}(), got ${c.length}`);return new Promise((f,x)=>{const d=ke.bind(null,{resolve:f,reject:x});c.push(d),l.sendMessage(...c)})},Ce={devtools:{network:{onRequestFinished:q(Te)}},runtime:{onMessage:q(te),onMessageExternal:q(te),sendMessage:ne.bind(null,"sendMessage",{minArgs:1,maxArgs:3})},tabs:{sendMessage:ne.bind(null,"sendMessage",{minArgs:2,maxArgs:3})}},D={clear:{minArgs:1,maxArgs:1},get:{minArgs:1,maxArgs:1},set:{minArgs:1,maxArgs:1}};return A.privacy={network:{"*":D},services:{"*":D},websites:{"*":D}},$(g,Ce,A)};r.exports=i(chrome)}})}(M)),M.exports}var de=xe();const ee=fe(de);function I(e,...s){}const pe={debug:(...e)=>I(console.debug,...e),log:(...e)=>I(console.log,...e),warn:(...e)=>I(console.warn,...e),error:(...e)=>I(console.error,...e)};class U extends Event{constructor(s,r){super(U.EVENT_NAME,{}),this.newUrl=s,this.oldUrl=r}static EVENT_NAME=j("wxt:locationchange")}function j(e){return`${ee?.runtime?.id}:geetest3:${e}`}function be(e){let s,r;return{run(){s==null&&(r=new URL(location.href),s=e.setInterval(()=>{let t=new URL(location.href);t.href!==r.href&&(window.dispatchEvent(new U(t,r)),r=t)},1e3))}}}class N{constructor(s,r){this.contentScriptName=s,this.options=r,this.abortController=new AbortController,this.isTopFrame?(this.listenForNewerScripts({ignoreFirstEvent:!0}),this.stopOldScripts()):this.listenForNewerScripts()}static SCRIPT_STARTED_MESSAGE_TYPE=j("wxt:content-script-started");isTopFrame=window.self===window.top;abortController;locationWatcher=be(this);receivedMessageIds=new Set;get signal(){return this.abortController.signal}abort(s){return this.abortController.abort(s)}get isInvalid(){return ee.runtime.id==null&&this.notifyInvalidated(),this.signal.aborted}get isValid(){return!this.isInvalid}onInvalidated(s){return this.signal.addEventListener("abort",s),()=>this.signal.removeEventListener("abort",s)}block(){return new Promise(()=>{})}setInterval(s,r){const t=setInterval(()=>{this.isValid&&s()},r);return this.onInvalidated(()=>clearInterval(t)),t}setTimeout(s,r){const t=setTimeout(()=>{this.isValid&&s()},r);return this.onInvalidated(()=>clearTimeout(t)),t}requestAnimationFrame(s){const r=requestAnimationFrame((...t)=>{this.isValid&&s(...t)});return this.onInvalidated(()=>cancelAnimationFrame(r)),r}requestIdleCallback(s,r){const t=requestIdleCallback((...i)=>{this.signal.aborted||s(...i)},r);return this.onInvalidated(()=>cancelIdleCallback(t)),t}addEventListener(s,r,t,i){r==="wxt:locationchange"&&this.isValid&&this.locationWatcher.run(),s.addEventListener?.(r.startsWith("wxt:")?j(r):r,t,{...i,signal:this.signal})}notifyInvalidated(){this.abort("Content script context invalidated"),pe.debug(`Content script "${this.contentScriptName}" context invalidated`)}stopOldScripts(){window.postMessage({type:N.SCRIPT_STARTED_MESSAGE_TYPE,contentScriptName:this.contentScriptName,messageId:Math.random().toString(36).slice(2)},"*")}verifyScriptStartedEvent(s){const r=s.data?.type===N.SCRIPT_STARTED_MESSAGE_TYPE,t=s.data?.contentScriptName===this.contentScriptName,i=!this.receivedMessageIds.has(s.data?.messageId);return r&&t&&i}listenForNewerScripts(s){let r=!0;const t=i=>{if(this.verifyScriptStartedEvent(i)){this.receivedMessageIds.add(i.data.messageId);const g=r;if(r=!1,g&&s?.ignoreFirstEvent)return;this.notifyInvalidated()}};addEventListener("message",t),this.onInvalidated(()=>removeEventListener("message",t))}}const we=Symbol("null");let ye=0;class ve extends Map{constructor(){super(),this._objectHashes=new WeakMap,this._symbolHashes=new Map,this._publicKeys=new Map;const[s]=arguments;if(s!=null){if(typeof s[Symbol.iterator]!="function")throw new TypeError(typeof s+" is not iterable (cannot read property Symbol(Symbol.iterator))");for(const[r,t]of s)this.set(r,t)}}_getPublicKeys(s,r=!1){if(!Array.isArray(s))throw new TypeError("The keys parameter must be an array");const t=this._getPrivateKey(s,r);let i;return t&&this._publicKeys.has(t)?i=this._publicKeys.get(t):r&&(i=[...s],this._publicKeys.set(t,i)),{privateKey:t,publicKey:i}}_getPrivateKey(s,r=!1){const t=[];for(let i of s){i===null&&(i=we);const g=typeof i=="object"||typeof i=="function"?"_objectHashes":typeof i=="symbol"?"_symbolHashes":!1;if(!g)t.push(i);else if(this[g].has(i))t.push(this[g].get(i));else if(r){const A=`@@mkm-ref-${ye++}@@`;this[g].set(i,A),t.push(A)}else return!1}return JSON.stringify(t)}set(s,r){const{publicKey:t}=this._getPublicKeys(s,!0);return super.set(t,r)}get(s){const{publicKey:r}=this._getPublicKeys(s);return super.get(r)}has(s){const{publicKey:r}=this._getPublicKeys(s);return super.has(r)}delete(s){const{publicKey:r,privateKey:t}=this._getPublicKeys(s);return!!(r&&super.delete(r)&&this._publicKeys.delete(t))}clear(){super.clear(),this._symbolHashes.clear(),this._publicKeys.clear()}get[Symbol.toStringTag](){return"ManyKeysMap"}get size(){return super.size}}new ve;function Ie(){}function F(e,...s){}const Ee={debug:(...e)=>F(console.debug,...e),log:(...e)=>F(console.log,...e),warn:(...e)=>F(console.warn,...e),error:(...e)=>F(console.error,...e)};return(async()=>{try{const{main:e,...s}=Ae,r=new N("geetest3",s);return await e(r)}catch(e){throw Ee.error('The content script "geetest3" crashed on startup!',e),e}})()}();
geetest3;
