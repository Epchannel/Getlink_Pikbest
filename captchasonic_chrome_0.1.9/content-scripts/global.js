var global=function(){"use strict";function a(n){return n}const o={matches:["https://newassets.hcaptcha.com/*"],allFrames:!0,match_about_blank:!1,run_at:"document_start",world:"MAIN",async main(){const n=Image;Image=function(){const r=new n;return r.crossOrigin="anonymous",r}}};function s(){}function t(n,...r){}const e={debug:(...n)=>t(console.debug,...n),log:(...n)=>t(console.log,...n),warn:(...n)=>t(console.warn,...n),error:(...n)=>t(console.error,...n)};return(async()=>{try{return await o.main()}catch(n){throw e.error('The content script "global" crashed on startup!',n),n}})()}();
global;
