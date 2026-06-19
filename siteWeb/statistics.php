<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Model Evaluation Statistics</title>
  <link rel="stylesheet" href="assets/css/style.css">
  <link rel="stylesheet" href="assets/css/navbar.css">

  <script src="assets/js/navbar.js"></script>


<style>
  :root {
    --blue:#0076CE; --orange:#e67e22; --green:#16a34a; --red:#dc3545; --muted:#888884;
    --surface:#ffffff; --bg:#f4f4f1; --border:#e4e4e0; --text:#1a1a1a;
  }
  body { background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; }
  .stats-wrap { max-width:900px; margin:0 auto; display:flex; flex-direction:column; gap:1.25rem; padding:1rem; }
  .stats-card { background:var(--surface); border:1px solid var(--border); border-radius:12px;
                box-shadow:0 1px 3px rgba(0,0,0,.05),0 4px 16px rgba(0,0,0,.04); padding:1.5rem; }
  .stats-card h1 { font-size:1.4rem; font-weight:600; margin:0 0 .6rem; }
  .stats-card h2 { font-size:1.1rem; font-weight:600; margin:0 0 .4rem; }
  .stats-card p  { color:#555; font-size:.93rem; line-height:1.6; margin:0 0 .4rem; }
  .stats-card .takeaway { background:#f0f7fc; border-left:3px solid var(--blue); padding:.6rem .9rem;
                border-radius:0 6px 6px 0; font-size:.9rem; color:#333; margin:.7rem 0 0; }
  .stats-card img { width:100%; height:auto; }
  table.metrics { width:100%; border-collapse:collapse; font-size:.92rem; margin-top:.5rem; }
  table.metrics th, table.metrics td { border:1px solid var(--border); padding:.55rem .75rem; text-align:left; }
  table.metrics th { background:var(--bg); font-weight:600; }
  table.metrics td:first-child { color:#555; }
  table.metrics .good { color:var(--green); font-weight:600; }
  table.metrics .bad  { color:var(--red); font-weight:600; }
  .chart-box { position:relative; }
  .back-link { display:inline-block; margin-bottom:.5rem; color:var(--blue); text-decoration:none; font-size:.9rem; }
  .back-link:hover { text-decoration:underline; }
  .note { font-size:.82rem; color:var(--muted); font-style:italic; margin-top:.5rem; }
  .legend-inline { font-size:.82rem; color:#666; margin-top:.3rem; }
</style>
</head>
<body>

<?php include("components/navbar.php"); ?>

<div class="stats-wrap">

  <div class="stats-card">
    <h1>Model Evaluation</h1>
    <p>This page shows how well the face-recognition system actually works, tested on two very
    different sets of photos. The first is our own <strong>custom set</strong>, taken on purpose
    under hard conditions: masks, hats, sunglasses, side views and poor lighting. The second is
    <strong>LFW</strong>, a well-known public set of clean, front-facing photos that researchers
    use as a common reference.</p>
    <p>The point is not to pick a winner, since the two sets are not comparable in size or difficulty.
    LFW tells us whether the system is <em>built correctly</em>, while the custom set tells us how it
    <em>copes with real, messy conditions</em>. The gap between the two is what we actually want
    to measure.</p>
    <div class="takeaway">In one line: on clean photos the system is reliable (EER 5.6%), and on
    deliberately hard photos it degrades (EER 26%). That contrast, not either number on its own,
    is the result.</div>
  </div>

  <div class="stats-card">
    <h2>The headline numbers</h2>
    <p>A few standard measures, side by side. <strong>EER</strong> is the error rate at the point
    where wrongly-accepted impostors and wrongly-rejected real users are balanced, where lower is
    better. <strong>AUC</strong> rates the overall ability to separate the two, where 1.0 is perfect and
    0.5 is a coin toss. <strong>d&prime;</strong> is how far apart the "same person" and "different
    person" scores sit, where higher is better. <strong>TAR @ FAR&le;1%</strong> answers the practical
    question "if we only tolerate 1 impostor in 100 getting through, how many real users do we
    still recognise?". The brackets are 95% confidence intervals: how much each number could
    shift given how many photos we tested on.</p>
    <table class="metrics">
      <tr><th>Metric</th><th>Custom (hard conditions)</th><th>LFW (benchmark)</th></tr>
      <tr><td>Real-user attempts</td><td>89</td><td>917</td></tr>
      <tr><td>Impostor attempts</td><td>16</td><td>298</td></tr>
      <tr><td>EER (95% CI)</td><td class="bad">26.0% [18.9, 43.2]</td><td class="good">5.6% [3.7, 7.0]</td></tr>
      <tr><td>AUC</td><td>0.638</td><td>0.979</td></tr>
      <tr><td>d&prime; (separability)</td><td>0.67</td><td>3.45</td></tr>
      <tr><td>TAR @ FAR&le;1%</td><td>n/a*</td><td class="good">87.7% (thr 0.6)</td></tr>
      <tr><td>Decision threshold</td><td>0.36</td><td>0.55</td></tr>
    </table>
    <p class="note">*With only 16 impostors, the false-accept rate can only change in jumps of
    about 6%. A budget as tight as 1% can only be reached by setting the threshold so high
    that no real user is accepted either, so this number is not meaningful for the custom set.
    This limitation disappears with LFW's 298 impostors.</p>
  </div>

  <div class="stats-card">
    <h2>How confident are these numbers?</h2>
    <p>This is the single most important chart on the page. Each bar is the EER (lower is better);
    the thin line on top is the 95% confidence interval. LFW's bar is low <em>and</em> its line is
    short, because we tested on over a thousand photos, so the number is trustworthy. The custom bar is
    high <em>and</em> its line is long, because with only about a hundred hard photos the true value
    could sit anywhere across a wide band. Reporting that wide band honestly is the point: a
    single "26%" alone would pretend to a precision we don't have.</p>
    <div class="chart-box" style="height:260px;"><canvas id="ci" role="img" aria-label="EER with confidence intervals"></canvas></div>
  </div>

  <div class="stats-card">
    <h2>Score distributions</h2>
    <p>Every comparison the system makes produces a similarity score between 0 and 1. Blue bars
    count the real matches (same person), orange bars the impostors (different people). When the
    two colours sit apart, a single cut-off can cleanly separate them. On the custom set (left)
    they overlap heavily in the middle, and that overlap is exactly why it struggles. On LFW (right)
    the two clusters barely touch.</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
      <div class="chart-box" style="height:240px;"><canvas id="distCustom" role="img" aria-label="Custom score distribution"></canvas></div>
      <div class="chart-box" style="height:240px;"><canvas id="distLfw" role="img" aria-label="LFW score distribution"></canvas></div>
    </div>
    <div class="takeaway">The overlap on the left is the <em>cause</em>, and the high error rate is
    the <em>effect</em>. Everything else on this page follows from how much these two colours mix.</div>
  </div>

  <div class="stats-card">
    <h2>ROC curves</h2>
    <p>This curve traces the trade-off as we move the decision threshold: across the bottom, how
    many impostors we wrongly let in; up the side, how many real users we correctly accept. A
    perfect system hugs the top-left corner. LFW (orange) climbs almost straight up to it; the
    custom curve (blue) stays much lower. The red dots mark each system's balance point (the EER).
    The custom line looks like a staircase because it was tested on few impostors, so it can only
    move in big steps. With hundreds of tests it would be smooth, like LFW.</p>
    <div class="chart-box" style="height:340px;"><canvas id="roc" role="img" aria-label="ROC curves custom vs LFW"></canvas></div>
  </div>

  <div class="stats-card">
    <h2>Results by photo condition (custom set)</h2>
    <p>This is where the custom set earns its keep: it splits every photo by what made it hard.
    Each bar shows three outcomes: correctly recognised (green), wrongly handled (orange), or
    discarded before any matching because the face was too hidden or turned away (red). Normal and
    glasses photos are almost all green; <strong>side views and masks</strong> pile up the orange
    and red. The overall error rate isn't spread evenly: it's driven by a few specific conditions.</p>
    <div class="chart-box" style="height:340px;"><canvas id="outcome" role="img" aria-label="Outcome per condition"></canvas></div>
  </div>

  <div class="stats-card">
    <h2>Why some photos were discarded</h2>
    <p>28 photos were set aside before any matching even started, for two reasons. Most
    (24) were turned away by a deliberate rule that refuses faces seen too far from the
    front, because lining them up to a standard template would be unreliable, so the system declines
    rather than guess. The rest (4) had no face found at all, usually when a mask or hat
    hid the eyes and nose the detector relies on. Both are intended behaviour, not a malfunction. The
    system choosing <em>not</em> to answer on a bad photo is safer than a confident wrong guess.</p>
    <div class="chart-box" style="height:280px;"><canvas id="fail" role="img" aria-label="Discards by condition and reason"></canvas></div>
  </div>

  <div class="stats-card">
    <h2>Who gets mistaken for whom</h2>
    <p>Each row is the real person; each column is who the system guessed. The dark diagonal means
    most people are identified correctly (68 of 89). The off-diagonal cells are the
    mix-ups, and they are not random: a handful of people have faces the system finds genuinely
    similar. The clearest case is <strong>Anthony Miranda mistaken for Florient Marchal (3 times)</strong>. These specific pairs, not a general
    weakness, are what a next version should target, whether with more enrolment photos per person, or a
    classifier trained to push confusable faces apart.</p>
    <div id="cmHeat" style="overflow-x:auto;"></div>
    <p class="note">The custom dataset is small (10 people), so the trend is clear but the
    exact cell counts carry the wide uncertainty shown in the confidence-interval chart above.</p>
  </div>

  <?php include("components/footer.php") ;?>


</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
const D = {"custom":{"n_g":89,"n_i":16,"eer":26.0,"eer_lo":18.9,"eer_hi":43.2,"auc":0.638,"auc_lo":0.489,"auc_hi":0.774,"thr":0.36,"dprime":0.67,"tar_eer":73.0,"tar_far1":null,"tar_far1_thr":null,"centers":[0.025,0.075,0.125,0.175,0.225,0.275,0.325,0.375,0.425,0.475,0.525,0.575,0.625,0.675,0.725,0.775,0.825,0.875,0.925,0.975],"hist_g":[0.0,0.0,0.0,0.0,0.0,0.225,0.899,2.697,4.494,3.596,3.596,1.798,0.899,0.449,0.225,0.225,0.0,0.225,0.674,0.0],"hist_i":[0.0,0.0,0.0,0.0,1.25,8.75,3.75,1.25,2.5,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.25,0.0,0.0,1.25],"roc_far":[1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,0.938,0.938,0.938,0.938,0.875,0.812,0.75,0.625,0.5,0.5,0.438,0.438,0.375,0.312,0.25,0.25,0.25,0.25,0.25,0.188,0.188,0.188,0.188,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.062,0.0,0.0,0.0],"roc_tar":[0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.764,0.753,0.753,0.742,0.73,0.719,0.708,0.697,0.64,0.629,0.584,0.539,0.483,0.438,0.416,0.382,0.36,0.303,0.27,0.225,0.18,0.157,0.146,0.112,0.101,0.09,0.079,0.067,0.056,0.045,0.022,0.022,0.022,0.022,0.011,0.011,0.011,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]},"lfw":{"n_g":917,"n_i":298,"eer":5.6,"eer_lo":3.7,"eer_hi":7.0,"auc":0.979,"auc_lo":0.97,"auc_hi":0.986,"thr":0.55,"dprime":3.45,"tar_eer":94.9,"tar_far1":87.7,"tar_far1_thr":0.6,"centers":[0.025,0.075,0.125,0.175,0.225,0.275,0.325,0.375,0.425,0.475,0.525,0.575,0.625,0.675,0.725,0.775,0.825,0.875,0.925,0.975],"hist_g":[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.044,0.327,0.545,1.483,2.443,3.206,4.449,4.515,2.137,0.698,0.065,0.087],"hist_i":[0.0,0.0,0.0,0.0,0.0,0.336,0.805,4.027,5.772,5.369,2.483,1.074,0.134,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"roc_far":[1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,0.997,0.993,0.99,0.983,0.983,0.983,0.98,0.97,0.963,0.943,0.926,0.889,0.852,0.809,0.742,0.681,0.611,0.567,0.51,0.453,0.403,0.369,0.292,0.238,0.185,0.154,0.121,0.091,0.07,0.06,0.023,0.02,0.017,0.017,0.007,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"roc_tar":[0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.986,0.986,0.981,0.98,0.977,0.975,0.969,0.964,0.96,0.956,0.949,0.94,0.929,0.908,0.896,0.877,0.858,0.832,0.809,0.79,0.756,0.731,0.694,0.663,0.632,0.595,0.544,0.508,0.453,0.413,0.374,0.327,0.287,0.226,0.18,0.148,0.119,0.098,0.074,0.057,0.041,0.032,0.025,0.015,0.013,0.007,0.005,0.004,0.004,0.003,0.003,0.002,0.001,0.0,0.0,0.0]},"outcome":{"conds":["glasses","hat","maskeyes","maskmouth","maskside","normal","side","sun"],"correct":[9,17,3,8,5,14,0,9],"wrong":[1,4,6,2,5,1,2,3],"discarded":[4,7,1,0,1,2,7,2]},"fail":{"conds":["glasses","hat","maskeyes","maskside","normal","side","sun","unknown"],"no_detection":[0,1,1,1,0,0,0,1],"rejected_alignment":[4,6,0,0,2,7,2,3]},"fail_total":28,"fail_reasons":{"no_detection":4,"rejected_alignment":24},"cm":{"labels":["anthony miranda","cl\u00e9mentine beaulieu","florient marchal","gabriel viard","kardiatou ba","lea carminati","mathis monnin","robin henry","sasha villemiane","sidney dachez"],"matrix":[[5,1,3,0,0,0,0,0,0,0],[0,6,1,0,0,1,0,1,1,0],[0,0,7,0,0,1,1,0,0,1],[0,0,0,7,0,0,1,0,1,0],[0,0,0,0,7,0,0,0,0,0],[0,0,0,0,0,8,0,0,0,0],[0,1,1,0,0,0,6,0,0,0],[0,0,2,0,1,0,0,6,0,0],[1,0,1,0,0,0,0,0,7,0],[0,0,0,0,0,1,0,0,0,9]],"max":9}};
const BLUE="#0076CE",ORANGE="#e67e22",GREEN="#16a34a",RED="#dc3545",MUTED="#888884";
const gridC="rgba(0,0,0,0.06)";

// EER + confidence interval bar chart (error bars drawn via a tiny plugin)
const ciErrorBars = {
  id:'ciErrorBars',
  afterDatasetsDraw(chart){
    const {ctx,scales:{y}}=chart; const meta=chart.getDatasetMeta(0);
    const lo=[D.custom.eer_lo,D.lfw.eer_lo], hi=[D.custom.eer_hi,D.lfw.eer_hi];
    ctx.save(); ctx.strokeStyle='#444'; ctx.lineWidth=1.5;
    meta.data.forEach((bar,i)=>{
      const x=bar.x, yl=y.getPixelForValue(lo[i]), yh=y.getPixelForValue(hi[i]);
      ctx.beginPath(); ctx.moveTo(x,yl); ctx.lineTo(x,yh);
      ctx.moveTo(x-7,yl); ctx.lineTo(x+7,yl);
      ctx.moveTo(x-7,yh); ctx.lineTo(x+7,yh); ctx.stroke();
    });
    ctx.restore();
  }
};
new Chart(document.getElementById('ci'),{type:'bar',
  data:{labels:['Custom (hard)','LFW (benchmark)'],datasets:[
    {label:'EER (%)',data:[D.custom.eer,D.lfw.eer],backgroundColor:[RED+'cc',GREEN+'cc'],
     borderColor:[RED,GREEN],borderWidth:1,barPercentage:0.5}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
    tooltip:{callbacks:{label:(c)=>{const k=c.dataIndex===0?D.custom:D.lfw;
      return 'EER '+k.eer+'%  (95% CI '+k.eer_lo+' to '+k.eer_hi+')';}}}},
    scales:{y:{beginAtZero:true,title:{display:true,text:'Equal Error Rate (%), lower is better',font:{size:11}},
      grid:{color:gridC},ticks:{font:{size:10}}},x:{grid:{display:false},ticks:{font:{size:11}}}}},
  plugins:[ciErrorBars]});

function distChart(id,ds){
  new Chart(document.getElementById(id),{type:'bar',
    data:{labels:ds.centers.map(c=>c.toFixed(2)),datasets:[
      {label:'Same person',data:ds.hist_g,backgroundColor:BLUE+'aa'},
      {label:'Different people',data:ds.hist_i,backgroundColor:ORANGE+'aa'}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{labels:{boxWidth:10,font:{size:11}}},title:{display:true,
        text:(id==='distCustom'?'Custom, d\u2032 '+D.custom.dprime:'LFW, d\u2032 '+D.lfw.dprime),font:{size:12}}},
      scales:{y:{title:{display:true,text:'Density',font:{size:11}},grid:{color:gridC},ticks:{font:{size:10}}},
        x:{title:{display:true,text:'Similarity score',font:{size:11}},grid:{color:gridC},
           ticks:{font:{size:9},maxRotation:0,autoSkip:true,maxTicksLimit:6}}}}});
}
distChart('distCustom',D.custom);
distChart('distLfw',D.lfw);

const rocEER = {
  id:'rocEER',
  afterDatasetsDraw(chart){
    const {ctx,scales:{x,y}}=chart;
    [[D.custom.eer/100,BLUE],[D.lfw.eer/100,GREEN]].forEach(([e,col])=>{
      // EER point sits where FAR = FRR, i.e. TAR = 1 - FAR = 1 - e, at FAR = e
      const px=x.getPixelForValue(e), py=y.getPixelForValue(1-e);
      ctx.save(); ctx.fillStyle=RED; ctx.strokeStyle='#fff'; ctx.lineWidth=1.5;
      ctx.beginPath(); ctx.arc(px,py,4,0,7); ctx.fill(); ctx.stroke(); ctx.restore();
    });
  }
};
new Chart(document.getElementById('roc'),{type:'line',
  data:{datasets:[
    {label:'Custom (AUC '+D.custom.auc+')',data:D.custom.roc_far.map((f,i)=>({x:f,y:D.custom.roc_tar[i]})),borderColor:BLUE,backgroundColor:BLUE,pointRadius:0,borderWidth:2,tension:0},
    {label:'LFW (AUC '+D.lfw.auc+')',data:D.lfw.roc_far.map((f,i)=>({x:f,y:D.lfw.roc_tar[i]})),borderColor:ORANGE,backgroundColor:ORANGE,pointRadius:0,borderWidth:2,tension:0},
    {label:'Random',data:[{x:0,y:0},{x:1,y:1}],borderColor:MUTED,borderDash:[5,5],pointRadius:0,borderWidth:1}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:10,font:{size:11}}}},
    scales:{x:{type:'linear',min:0,max:1,title:{display:true,text:'False Accept Rate (impostors let in)',font:{size:11}},grid:{color:gridC},ticks:{font:{size:10}}},
      y:{min:0,max:1,title:{display:true,text:'True Accept Rate (real users recognised)',font:{size:11}},grid:{color:gridC},ticks:{font:{size:10}}}}},
  plugins:[rocEER]});

new Chart(document.getElementById('outcome'),{type:'bar',
  data:{labels:D.outcome.conds,datasets:[
    {label:'Correct',data:D.outcome.correct,backgroundColor:GREEN},
    {label:'Wrong',data:D.outcome.wrong,backgroundColor:ORANGE},
    {label:'Discarded',data:D.outcome.discarded,backgroundColor:RED}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:10,font:{size:11}}}},
    scales:{y:{title:{display:true,text:'Number of photos',font:{size:11}},grid:{color:gridC},ticks:{font:{size:10},stepSize:2}},
      x:{ticks:{font:{size:10},maxRotation:40,minRotation:30,autoSkip:false}}}}});

new Chart(document.getElementById('fail'),{type:'bar',
  data:{labels:D.fail.conds,datasets:[
    {label:'rejected (too far from front)',data:D.fail.rejected_alignment,backgroundColor:BLUE},
    {label:'no face detected',data:D.fail.no_detection,backgroundColor:MUTED}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:10,font:{size:11}}}},
    scales:{y:{stacked:true,title:{display:true,text:'Discarded photos',font:{size:11}},grid:{color:gridC},ticks:{font:{size:10},stepSize:1}},
      x:{stacked:true,ticks:{font:{size:10},maxRotation:40,minRotation:30,autoSkip:false}}}}});

const cm=D.cm,mx=cm.max;
let h='<table style="border-collapse:collapse;font-size:10px;"><tr><th></th>';
cm.labels.forEach(l=>{h+='<th style="padding:2px 3px;writing-mode:vertical-rl;transform:rotate(180deg);color:'+MUTED+';font-weight:400;white-space:nowrap;height:80px;">'+l+'</th>';});
h+='</tr>';
cm.matrix.forEach((row,i)=>{
  h+='<tr><td style="padding:2px 6px;text-align:right;color:'+MUTED+';white-space:nowrap;">'+cm.labels[i]+'</td>';
  row.forEach((v,j)=>{const a=v===0?0:0.15+0.85*(v/mx);
    const isDiag=i===j; const base=isDiag?'22,163,74':'220,53,69';
    const col=v===0?'transparent':'rgba('+base+','+a+')';
    const txt=a>0.5?'#fff':(v===0?'#ccc':'#1a1a1a');
    h+='<td style="width:26px;height:26px;text-align:center;background:'+col+';color:'+txt+';border:0.5px solid #eee;">'+(v||'')+'</td>';});
  h+='</tr>';});
h+='</table>';
h+='<div class="legend-inline">Green = correct (diagonal). Red = a mix-up: the row person guessed as the column person.</div>';
document.getElementById('cmHeat').innerHTML=h;
</script>
</body>
</html>