// Datos y cálculo compartidos de las páginas de exploración (30 planes de DATOS_EJEMPLO_30_PLANES.csv)
(function(){
const UF=41309.19;
const P=[
    ['Consalud','13-RET10-26','RET NACIONAL 10 01 26','Prestador preferente',50,50,3500,0.93,0.731,'202601'],
    ['Consalud','13-RCORE10-26','RET CORE 10 01 26','Prestador preferente',40,60,3500,0.93,0.731,'202601'],
    ['Banmédica','BSCC260100','SALUD CONECTA CLASICO 00/2601','Plan cerrado',40,40,5000,0.94,0.778,'202601'],
    ['Consalud','13-RCORE20-26','RET CORE 20 01 26','Prestador preferente',40,60,3500,1.01,0.731,'202601'],
    ['Consalud','13-RET20-26','RET NACIONAL 20 01 26','Prestador preferente',50,60,3500,1.05,0.731,'202601'],
    ['Banmédica','BSCC260102','SALUD CONECTA CLASICO 02/2601','Plan cerrado',50,40,5000,1.0,0.778,'202601'],
    ['Banmédica','BSCC260122','SALUD CONECTA CLASICO 22/2601','Plan cerrado',50,50,5000,1.05,0.778,'202601'],
    ['Consalud','13-CORE101-26','CORE 10 01 26','Prestador preferente',40,60,3900,1.16,0.731,'202601'],
    ['Banmédica','BSCC260104','SALUD CONECTA CLASICO 04/2601','Plan cerrado',60,40,5000,1.11,0.778,'202601'],
    ['Consalud','13-RCORE30-26','RET CORE 30 01 26','Prestador preferente',50,60,3500,1.2,0.731,'202601'],
    ['Colmena','SR1267050','SILVER LT 1267050','Prestador preferente',90,60,6500,1.25,1.036,'202608'],
    ['Colmena','SR1268050','SILVER LT 1268050','Prestador preferente',100,60,6500,1.28,1.036,'202608'],
    ['Nueva Masvida','PPS2450R','PLENO SALUD PPS2450R','Prestador preferente',90,60,4500,1.48,0.854,'202405'],
    ['Colmena','SR1267060','SILVER LT 1267060','Prestador preferente',90,70,6500,1.3,1.036,'202608'],
    ['Colmena','SR1269050','SILVER LT 1269050','Prestador preferente',100,60,6500,1.31,1.036,'202608'],
    ['Colmena','SR1268060','SILVER LT 1268060','Prestador preferente',100,70,6500,1.33,1.036,'202608'],
    ['Colmena','SR12610050','SILVER LT 12610050','Prestador preferente',100,60,6500,1.34,1.036,'202608'],
    ['Cruz Blanca','CMBX018D25','CAMPUS BUPA MAX 1800 D25','Plan cerrado',90,60,1750,1.41,0.971,'202512'],
    ['Colmena','ST3268060','COLMENA STAR 3268060','Prestador preferente',90,60,5500,1.35,1.036,'202607'],
    ['Colmena','ST4268060','COLMENA STAR 4268060','Prestador preferente',90,60,5500,1.35,1.036,'202609'],
    ['Vida Tres','VPRPO260779','VANGUARDIA PREMIUM PLATINUM ONE 79/2607','Prestador preferente',100,80,11000,2.76,0.712,'202607'],
    ['Colmena','LP1269050','COLMENA PRO LT 1269050','Prestador preferente',90,50,8500,3.99,1.036,'202604'],
    ['Cruz Blanca','CBMR018526','CAMPUS BUPA REGIONAL 1800 526','Prestador preferente',100,80,6000,2.54,0.971,'202605'],
    ['Colmena','EL1265050','COLMENA ELITE 1265050','Prestador preferente',70,70,7500,2.1,1.036,'202512'],
    ['Vida Tres','VPRPO26071012','VANGUARDIA PREMIUM PLATINUM ONE 1012/2607','Prestador preferente',100,80,11000,4.68,0.712,'202607'],
    ['Cruz Blanca','OPR1114D25','ON PROTECCION 1 REGIONAL 1400 D25','Prestador preferente',100,70,5000,2.33,0.971,'202512'],
    ['Cruz Blanca','ONPR209D25','ON PROTECCION 2 900 D25','Prestador preferente',80,80,7000,2.89,0.971,'202512'],
    ['Colmena','ST4266070','COLMENA STAR 4266070','Prestador preferente',70,70,5500,1.28,1.036,'202609'],
    ['Nueva Masvida','PPS2470R','PLENO SALUD PPS2470R','Prestador preferente',100,60,4500,1.6,0.854,'202405'],
    ['Cruz Blanca','CBMR026D25','CAMPUS BUPA REGIONAL 2600 D25','Prestador preferente',60,70,7000,3.28,0.971,'202512'],
  ];
const FACT=[[0,1,0.6,0.0],[2,19,0.6,0.6],[20,24,0.9,0.7],[25,34,1.0,0.7],[35,44,1.3,0.9],[45,54,1.4,1.0],[55,64,2.0,1.4],[65,120,2.4,2.2]];
const MESES=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const fmt=(n,d=2)=>{const s=Number(n).toFixed(d);let[i,f]=s.split('.');i=i.replace(/\B(?=(\d{3})+(?!\d))/g,'.');return f?i+','+f:i;};
const clp=n=>'$'+fmt(Math.round(n),0);
const ff=f=>String(f).replace('.',',');
const factor=(e,t)=>{const r=FACT.find(r=>e>=r[0]&&e<=r[1])||FACT[7];return t==='cotizante'?r[2]:r[3];};
const mes=a=>MESES[+a.slice(4,6)-1]+' '+a.slice(0,4);
function members(g){const o=[{rol:'titular',tipo:'cotizante',edad:g.titular.edad,sexo:g.titular.sexo}];
 if(g.conyuge)o.push({rol:'conyuge',tipo:g.conyuge.cond,edad:g.conyuge.edad,sexo:g.conyuge.sexo});
 g.cargas.forEach(c=>o.push({rol:'carga',tipo:'carga',edad:c.edad,sexo:c.sexo}));
 return o.map(m=>{const nino=m.rol==='carga'&&m.edad<18;const q=nino?(m.edad<2?'Guagua':(m.sexo==='H'?'Niño':'Niña')):(m.sexo==='H'?'Hombre':'Mujer');
  return {...m,f:factor(m.edad,m.tipo),q,quien:q+', '+m.edad+(m.edad===1?' año':' años'),corto:q+' '+m.edad+(m.rol==='conyuge'?' ('+m.tipo+')':''),rolTxt:m.rol==='titular'?'Titular':m.rol==='conyuge'?'Cónyuge':'Carga'};});}
function plans(g,w){const mem=members(g),sf=mem.reduce((a,m)=>a+m.f,0),n=mem.length;
 const all=P.map(p=>{const uf=Math.round((p[7]*sf+p[8]*n)*100-1e-6)/100;return{isapre:p[0],codigo:p[1],nombre:p[2],modalidad:p[3],hosp:p[4],amb:p[5],tope:p[6],base:p[7],ges:p[8],inicio:p[9],uf,clp:Math.round(uf*UF)};});
 w=w||{precio:20,hosp:35,amb:20,tope:25};const mm=k=>{const v=all.map(p=>p[k]);return[Math.min(...v),Math.max(...v)];};
 const[a1,b1]=mm('uf'),[a2,b2]=mm('hosp'),[a3,b3]=mm('amb'),[a4,b4]=mm('tope');const t=(w.precio+w.hosp+w.amb+w.tope)||1;
 all.forEach(p=>{p.score=(w.precio*(1-(p.uf-a1)/(b1-a1+1e-9))+w.hosp*(p.hosp-a2)/(b2-a2+1e-9)+w.amb*(p.amb-a3)/(b3-a3+1e-9)+w.tope*(p.tope-a4)/(b4-a4+1e-9))/t;
  p.sem=p.score>=.75?{k:'good',label:'Buen ajuste',bg:'#CFEAD9',fg:'#0F5B57'}:p.score>=.55?{k:'mid',label:'Ajuste medio',bg:'#F4E9DB',fg:'#2E3B38'}:{k:'low',label:'Ajuste bajo',bg:'#F7E4DE',fg:'#9A3F2B'};});
 const min=Math.min(...all.map(p=>p.uf)),max=Math.max(...all.map(p=>p.uf));
 all.forEach(p=>{p.best=p.uf===min;});
 return{all,mem,sf,n,min,max};}
window.ALC={UF,P,fmt,clp,ff,factor,mes,members,plans,DEF:{titular:{edad:39,sexo:'H'},conyuge:{edad:38,sexo:'M',cond:'carga'},cargas:[{edad:7,sexo:'H'}]}};
})();
