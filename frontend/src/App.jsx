import React, { useEffect, useRef, useState } from 'react';
import {
  Activity, ArrowLeft, ArrowRight, BarChart3, BookOpen, Check, CheckCircle2,
  ChevronRight, ClipboardCheck, Clock3, Database, Download, Eye, EyeOff,
  FileQuestion, FileText, Flag, Gauge, Home, Info, Layers3, LockKeyhole,
  LogOut, Menu, PlayCircle, RotateCcw, ShieldCheck, Sparkles, Target,
  Timer, Trophy, UserRound, Users, X, XCircle
} from 'lucide-react';
import { api } from './api.js';

const initials = (name = 'C') => name.split(/\s+/).map(s => s[0]).join('').slice(0, 2).toUpperCase();
const percent = (score, possible) => possible ? Math.round((score / possible) * 100) : 0;
const timeLabel = (seconds) => {
  const s = Math.max(0, seconds);
  return [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60]
    .map(x => String(x).padStart(2, '0')).join(':');
};
const durationLabel = (seconds) => seconds >= 3600
  ? Math.floor(seconds / 3600) + 'h ' + Math.round((seconds % 3600) / 60) + 'm'
  : Math.max(1, Math.ceil(seconds / 60)) + ' min';

function Brand({ compact = false }) {
  return <div className={'brand ' + (compact ? 'brand-small' : '')}>
    <div className="brand-logo"><Database size={27} strokeWidth={2.7}/><ShieldCheck size={16} className="logo-shield"/></div>
    <div><b>Technical Quiz</b><span>DBA & Data Governance</span></div>
  </div>;
}
function Pill({ children, tone = 'blue' }) { return <span className={'pill pill-' + tone}>{children}</span>; }
function ProgressBar({ value, tone = 'blue' }) {
  return <div className="progress-track" role="progressbar" aria-valuenow={Math.min(100,Math.max(0,value))} aria-valuemin="0" aria-valuemax="100">
    <div className={'progress-fill fill-' + tone} style={{width: Math.min(100,Math.max(0,value)) + '%'}} />
  </div>;
}
function Stat({ icon: Icon, value, label, tone = 'blue' }) {
  return <div className="stat-card"><div className={'icon-bubble bubble-' + tone}><Icon size={26}/></div>
    <div><div className="stat-value">{value}</div><div className="muted">{label}</div></div></div>;
}
const navigation = [
  { id: 'overview', label: 'Overview', icon: Home },
  { id: 'quiz', label: 'Start Quiz', icon: PlayCircle },
  { id: 'result', label: 'My Result', icon: BarChart3 },
  { id: 'instructions', label: 'Instructions', icon: BookOpen },
];

function Sidebar({ page, user, onNavigate, mobileOpen, setMobileOpen }) {
  const links = user?.is_staff ? [...navigation, { id:'admin', label:'HR Dashboard', icon: Users }] : navigation;
  return <>
    <div className={'mobile-shade ' + (mobileOpen ? 'show' : '')} onClick={() => setMobileOpen(false)} />
    <aside className={'sidebar ' + (mobileOpen ? 'sidebar-open' : '')}>
      <Brand />
      <nav aria-label="Primary navigation">
        {links.map(({id,label,icon:Icon}) =>
          <button key={id} className={'side-link ' + (page === id ? 'active' : '')}
            aria-current={page===id?'page':undefined} onClick={()=>{onNavigate(id);setMobileOpen(false);}}>
            <Icon size={20}/><span>{label}</span>
          </button>)}
      </nav>
      <div className="sidebar-foot"><div className="sidebar-orb"><Database size={54}/><ShieldCheck size={27}/></div>
        <div>Make every answer count.</div><small>Secure skills assessment</small></div>
    </aside>
  </>;
}

function LoginPage({ onLogin, busy, error }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  return <div className="auth-page"><div className="auth-shell">
    <div className="auth-art">
      <Brand />
      <div className="auth-art-content">
        <div className="auth-art-icon"><ClipboardCheck size={64} strokeWidth={1.5}/><ShieldCheck size={34}/></div>
        <div className="eyebrow pale">ONLINE TECHNICAL ASSESSMENT</div>
        <h1>Show what you know.<br/>Grow where you lead.</h1>
        <p>A simple, focused assessment for DBA and Data Governance professionals.</p>
        <div className="auth-points"><span><CheckCircle2 size={16}/> 25 targeted questions</span>
          <span><Clock3 size={16}/> 60-minute assessment</span>
          <span><ShieldCheck size={16}/> Secure results</span></div>
      </div>
      <div className="auth-art-bottom">Simplicity <span>·</span> Velocity <span>·</span> Efficiency</div>
    </div>
    <div className="auth-panel"><div className="auth-panel-inner">
      <div className="auth-welcome-icon"><LockKeyhole size={24}/></div>
      <h2>Welcome back</h2><p className="muted">Sign in to continue your assessment.</p>
      <form onSubmit={e=>{e.preventDefault();onLogin(username,password);}}>
        <label htmlFor="username">Username</label>
        <div className="input-wrapper"><UserRound size={19}/><input id="username" autoComplete="username"
          autoFocus required value={username} onChange={e=>setUsername(e.target.value)}
          placeholder="Enter your username"/></div>
        <label htmlFor="password">Password</label>
        <div className="input-wrapper"><LockKeyhole size={19}/><input id="password" autoComplete="current-password"
          type={show?'text':'password'} required value={password}
          onChange={e=>setPassword(e.target.value)} placeholder="Enter your password"/>
          <button type="button" className="icon-plain" aria-label={show?'Hide password':'Show password'}
            onClick={()=>setShow(!show)}>{show?<EyeOff size={18}/>:<Eye size={18}/>}</button></div>
        {error && <div className="alert error" role="alert">{error}</div>}
        <button className="btn primary full auth-submit" disabled={busy} type="submit">
          {busy?'Signing in…':'Sign in'} <ArrowRight size={18}/></button>
      </form>
      <div className="auth-help"><ShieldCheck size={17}/> Access is provisioned by your assessor.<br/>
        Contact the recruitment team for login assistance.</div>
    </div></div>
  </div><div className="auth-copyright">DBA & Data Governance · Candidate Assessment Portal</div></div>;
}

function OverviewPage({ quiz, onStart, isResuming, hasResult, onResult }) {
  const dba = quiz.domains.find(d=>d.name==='DBA');
  const dg = quiz.domains.find(d=>d.name==='Data Governance');
  return <div className="page-stack">
    <section className="hero hero-overview">
      <div><div className="eyebrow">WELCOME TO YOUR ASSESSMENT</div>
        <h1>DBA & <span>Data Governance</span><br/>Technical Quiz</h1>
        <p>Assess your knowledge and practical skills in database administration and trusted data management.</p>
      </div>
      <div className="hero-illustration"><Database size={94} strokeWidth={1.5}/><ShieldCheck size={68}/><BarChart3 size={66}/></div>
    </section>
    <section className="stat-grid">
      <Stat icon={ClipboardCheck} value={quiz.question_count} label="Questions"/>
      <Stat icon={Trophy} value={quiz.possible_score + '%'} label="Total score" tone="amber"/>
      <Stat icon={Clock3} value={quiz.duration_minutes + ' min'} label="Time limit" tone="purple"/>
    </section>
    <section className="panel coverage">
      <div className="section-title"><Target size={21}/><h2>Topic coverage</h2></div>
      <div className="coverage-grid">
        <div className="coverage-card coverage-dba"><div className="coverage-heading">
          <div className="icon-bubble bubble-blue"><Database size={28}/></div>
          <div><h3>DBA</h3><p>Database administration, performance, backup and recovery, security, and more.</p></div>
          <Pill>{Math.round(dba.points / quiz.possible_score * 100)}%</Pill></div>
          <ProgressBar value={dba.points / quiz.possible_score * 100}/><small>{dba.questions} questions · {dba.points} points</small></div>
        <div className="coverage-card coverage-governance"><div className="coverage-heading">
          <div className="icon-bubble bubble-green"><ShieldCheck size={28}/></div>
          <div><h3>Data Governance</h3><p>Data ownership, quality, lineage, classification, MDM and governance controls.</p></div>
          <Pill tone="green">{Math.round(dg.points / quiz.possible_score * 100)}%</Pill></div>
          <ProgressBar value={dg.points / quiz.possible_score * 100} tone="green"/><small>{dg.questions} questions · {dg.points} points</small></div>
      </div>
      <div className="section-title steps-title"><Sparkles size={21}/><h2>How it works</h2></div>
      <div className="steps"><div className="step"><div className="step-icon bubble-blue"><ClipboardCheck/></div>
        <div><b>1. Take the quiz</b><p>Answer 25 multiple-choice questions.</p></div></div>
        <ChevronRight className="step-arrow"/><div className="step"><div className="step-icon bubble-purple"><Timer/></div>
          <div><b>2. Submit</b><p>Finish within 60 minutes.</p></div></div>
        <ChevronRight className="step-arrow"/><div className="step"><div className="step-icon bubble-green"><BarChart3/></div>
          <div><b>3. View your result</b><p>See your score and topic summary.</p></div></div>
      </div>
    </section>
    <div className="page-cta">
      <button className="btn primary large" onClick={onStart}><PlayCircle size={22}/>
        {isResuming?'Resume Assessment':'Start Assessment'}<ArrowRight size={21}/></button>
      {hasResult && <button className="btn outline" onClick={onResult}><BarChart3 size={19}/> View Result</button>}
    </div>
  </div>;
}

function InstructionsPage({ quiz, onStart, isResuming }) {
  return <div className="page-stack">
    <section className="page-heading">
      <div><div className="eyebrow">BEFORE YOU BEGIN</div><h1>Quiz Instructions</h1>
        <p>Please read the following information carefully before starting your assessment.</p></div>
      <div className="heading-art"><ClipboardCheck size={70}/><ShieldCheck size={49}/></div>
    </section>
    <div className="instruction-columns">
      <section className="panel instruction-panel"><div className="section-title blue-banner"><Target size={22}/><h2>Quiz details</h2></div>
        <div className="instruction-stats"><div><ClipboardCheck/><b>{quiz.question_count}</b><span>Questions</span></div>
          <div><Timer/><b>{quiz.duration_minutes}</b><span>Minutes</span></div>
          <div><Trophy/><b>{quiz.possible_score}%</b><span>Total score</span></div></div>
        <div className="section-title bordered"><Layers3 size={21}/><h2>Question format</h2></div>
        <div className="format-strip"><FileQuestion size={36}/><div><b>Multiple choice</b>
          <p>Select one best answer (A, B, C or D) for each question. Each question is worth 4 points.</p></div></div>
        <div className="section-title bordered"><Gauge size={21}/><h2>Topic coverage</h2></div>
        <div className="mini-topics"><div><Database size={26}/><b>DBA</b><span>13 questions · 52%</span></div>
          <div><ShieldCheck size={26}/><b>Data Governance</b><span>12 questions · 48%</span></div></div>
      </section>
      <section className="panel instruction-panel"><div className="section-title blue-banner"><ShieldCheck size={22}/><h2>Rules & guidelines</h2></div>
        <div className="rule-list">
          <div><span className="rule-icon bubble-blue"><Activity/></span><p>Use a stable internet connection while taking the assessment.</p></div>
          <div><span className="rule-icon bubble-red"><XCircle/></span><p>Avoid closing the browser. Your saved answers can be resumed before the deadline.</p></div>
          <div><span className="rule-icon bubble-purple"><Clock3/></span><p>The timer starts once you begin. Time is enforced by the server.</p></div>
          <div><span className="rule-icon bubble-green"><ArrowRight/></span><p>You may navigate between questions and change answers before submission.</p></div>
          <div><span className="rule-icon bubble-amber"><Info/></span><p>Submission is final. Unanswered questions receive zero points.</p></div>
          <div><span className="rule-icon bubble-blue"><LockKeyhole/></span><p>Results are recorded securely. Retakes require assessor authorization.</p></div>
        </div>
      </section>
    </div>
    <section className="ready-banner"><div className="ready-icon"><Flag size={30}/></div>
      <div><h2>Ready to begin?</h2><p>You can complete the quiz at your own pace within the time limit.</p></div>
      <button className="btn primary" onClick={onStart}><PlayCircle size={21}/>{isResuming?'Resume Quiz':'Start Quiz'}<ArrowRight size={19}/></button>
    </section>
  </div>;
}

function QuizPage({ attempt, currentIndex, setCurrentIndex, onAnswer, saving, onSubmit, timeLeft, submitting }) {
  const questions = attempt.questions;
  const q = questions[currentIndex];
  const selected = attempt.answers[String(q.id)];
  const answered = questions.filter(x=>Boolean(attempt.answers[String(x.id)])).length;
  const progress = answered / questions.length * 100;
  return <div className="page-stack">
    <section className="exam-topbar"><div><div className="eyebrow">YOUR TECHNICAL ASSESSMENT</div>
      <h1>DBA & Data Governance Quiz</h1><p>{questions.length} questions <span className="dot-sep">•</span> Total score: 100% <span className="dot-sep">•</span> 60-minute time limit</p></div>
      <div className={'timer-card ' + (timeLeft < 300 ? 'timer-warning' : '')}>
        <Clock3 size={25}/><div><span>Time remaining</span><strong>{timeLabel(timeLeft)}</strong></div></div>
    </section>
    <div className="exam-grid">
      <section className="panel question-card">
        <div className="question-strip"><span>Question {currentIndex + 1} of {questions.length}</span>
          <div><Pill tone={q.domain === 'DBA'?'blue':'green'}>{q.domain}</Pill><small>({q.points} Points)</small></div></div>
        <div className="question-topic">{q.topic}</div>
        <h2>{q.text}</h2>
        <fieldset disabled={saving !== null || submitting} className="options-fieldset">
          <legend className="sr-only">Select one answer</legend>
          {q.options.map(opt => <label className={'answer-option ' + (selected === opt.code ? 'selected' : '')} key={opt.code}>
            <input type="radio" name={'question-' + q.id} checked={selected === opt.code}
              onChange={()=>onAnswer(q.id,opt.code)}/>
            <span className="answer-radio" aria-hidden="true"></span>
            <b>{opt.code}.</b><span>{opt.text}</span>
          </label>)}
        </fieldset>
        <div className="question-actions"><span className="save-status">{saving === q.id ? 'Saving answer…'
          : selected ? <><Check size={16}/> Answer saved</> : 'Select your answer to continue'}</span>
          <div className="question-buttons"><button className="btn outline" disabled={currentIndex === 0}
            onClick={()=>setCurrentIndex(currentIndex-1)}><ArrowLeft size={17}/> Previous</button>
            {currentIndex < questions.length-1 ?
              <button className="btn primary" onClick={()=>setCurrentIndex(currentIndex+1)}>Next <ArrowRight size={18}/></button>
              : <button className="btn primary" disabled={saving!==null || submitting} onClick={()=>onSubmit(false)}>Finish Quiz <CheckCircle2 size={18}/></button>}
          </div>
        </div>
      </section>
      <aside className="panel navigator">
        <div className="nav-section"><div className="nav-heading"><b>Quiz Progress</b><span>{answered} / {questions.length} answered</span></div>
          <ProgressBar value={progress} tone="green"/><div className="percent-label">{Math.round(progress)}% complete</div></div>
        <div className="nav-section"><div className="nav-heading"><b>Question Navigator</b><Info size={18}/></div>
          <div className="number-grid">{questions.map((item,index)=>{
            const isAnswered=Boolean(attempt.answers[String(item.id)]);
            return <button key={item.id} className={'number-cell ' +
              (index === currentIndex?'current':isAnswered?'answered':'')}
              aria-label={'Question '+(index+1)+(isAnswered?', answered':', unanswered')}
              aria-current={index===currentIndex?'step':undefined}
              onClick={()=>setCurrentIndex(index)}>{index+1}{isAnswered && index!==currentIndex?<Check size={11}/>:null}</button>;
          })}</div>
          <div className="nav-legend"><span><i className="legend-answered"/>Answered</span>
            <span><i className="legend-current"/>Current</span><span><i/>Not answered</span></div>
        </div>
        <div className="nav-submit"><button className="btn submit full" disabled={submitting || saving!==null}
          onClick={()=>onSubmit(false)}><CheckCircle2 size={20}/>{submitting?'Submitting…':'Submit Quiz'}</button>
          <small>Review your selections before submitting.</small></div>
      </aside>
    </div>
  </div>;
}

function ResultPage({ data, onOverview, showReview, setShowReview, onRetake }) {
  if (!data) return <section className="panel empty-state"><BarChart3 size={46}/><h2>No results yet</h2>
    <p>Your completed assessment and scores will appear here.</p><button className="btn primary" onClick={onOverview}>Go to overview <ArrowRight size={18}/></button></section>;
  const wrong = data.total_questions - data.correct_count;
  return <div className="page-stack">
    <section className="hero result-hero"><div className="hero-status"><CheckCircle2 size={36}/>
      <div><h1>Assessment Completed!</h1><p>DBA & Data Governance Assessment</p></div></div>
      <div className="result-hero-trophy"><Trophy size={86}/></div>
    </section>
    <div className="results-grid">
      <section className="panel result-score">
        <div className="score-ring" style={{'--percent':data.percent}}><div><strong>{data.percent}%</strong><span>({data.score} / {data.possible_score})</span></div></div>
        <span className={'result-status ' + (data.passed?'pass':'needs-work')}>
          {data.passed?<CheckCircle2 size={19}/>:<Info size={19}/>}
          {data.passed?'Pass':'Needs improvement'}</span>
        <div className="result-facts">
          <div><FileQuestion/><span>Total questions</span><strong>{data.total_questions}</strong></div>
          <div><CheckCircle2/><span>Correct answers</span><strong>{data.correct_count}</strong></div>
          <div><XCircle/><span>Incorrect / unanswered</span><strong>{wrong}</strong></div>
          <div><Clock3/><span>Time taken</span><strong>{durationLabel(data.time_taken_seconds)}</strong></div>
        </div>
      </section>
      <div className="results-detail">
        <div className="domain-grid">{data.domains.map(d=><section className={'domain-card '+(d.name==='DBA'?'domain-dba':'domain-dg')} key={d.name}>
          <div className={'icon-bubble '+(d.name==='DBA'?'bubble-blue':'bubble-green')}>{d.name==='DBA'?<Database size={28}/>:<ShieldCheck size={28}/>}</div>
          <div><h3>{d.name}</h3><span className="muted">{d.questions} Questions · {d.score}/{d.possible} points</span>
            <ProgressBar value={percent(d.score,d.possible)} tone={d.name==='DBA'?'blue':'green'}/></div>
          <Pill tone={d.name==='DBA'?'blue':'green'}>{percent(d.score,d.possible)}%</Pill>
        </section>)}</div>
        <section className="panel topic-panel"><div className="section-title"><Layers3 size={21}/><h2>Topic performance</h2></div>
          <div className="topic-table-wrap"><table className="topic-table"><thead><tr>
            <th>#</th><th>Topic</th><th>Questions</th><th>Score</th><th>Progress</th></tr></thead>
            <tbody>{data.topics.map((t,i)=><tr key={t.name}>
              <td>{i+1}</td><td>{t.name}</td><td>{t.questions}</td>
              <td><Pill tone={t.correct===t.questions?'green':'blue'}>{percent(t.score,t.possible)}%</Pill></td>
              <td className="mini-bar"><ProgressBar value={percent(t.score,t.possible)} tone={t.correct===t.questions?'green':'blue'}/></td>
            </tr>)}</tbody></table></div>
        </section>
      </div>
    </div>
    {showReview && data.review_available && <section className="panel review-panel">
      <div className="section-title"><FileText size={21}/><h2>Answer review</h2></div>
      {data.review.map(q=><div className="review-item" key={q.id}>
        <b>{q.number}. {q.text}</b><p>Your answer: {q.selected_code || 'Not answered'} · Correct answer: {q.correct_code}</p>
        <small>{q.explanation}</small></div>)}</section>}
    <div className="page-cta">
      {data.review_available && <button className="btn primary" onClick={()=>setShowReview(!showReview)}>
        <FileText size={19}/>{showReview?'Hide Answers':'Review Answers'}</button>}
      <button className="btn outline" onClick={onRetake}><RotateCcw size={18}/> Retake Quiz</button>
      <button className="btn outline" onClick={()=>window.print()}><Download size={19}/> Save Result as PDF</button>
    </div>
    <p className="result-note">Results are confidential and available only to you and authorized assessors.</p>
  </div>;
}

function AdminPage({ adminData, loading, onRefresh }) {
  if (loading && !adminData) return <div className="loading-card">Loading recruitment dashboard…</div>;
  if (!adminData) return <div className="empty-state">Unable to load dashboard.</div>;
  return <div className="page-stack">
    <section className="page-heading"><div><div className="eyebrow">ASSESSOR WORKSPACE</div><h1>Candidate Dashboard</h1>
      <p>Monitor assessment outcomes and download candidate results.</p></div><Users size={58} className="heading-icon"/></section>
    <section className="stat-grid admin-stats">
      <Stat icon={Users} value={adminData.total_candidates} label="Candidates"/>
      <Stat icon={ClipboardCheck} value={adminData.total_attempts} label="Attempts" tone="purple"/>
      <Stat icon={CheckCircle2} value={adminData.completed_attempts} label="Completed" tone="green"/>
      <Stat icon={BarChart3} value={adminData.average_score+'%'} label="Average score" tone="amber"/>
    </section>
    <section className="panel admin-panel">
      <div className="admin-panel-top"><div className="section-title"><FileText size={21}/><h2>Assessment results</h2></div>
        <div className="admin-actions"><button className="btn outline compact" onClick={onRefresh}><RotateCcw size={17}/> Refresh</button>
          <a className="btn primary compact" href="/api/admin/results.csv"><Download size={17}/> Export CSV</a></div></div>
      <div className="topic-table-wrap"><table className="topic-table admin-table"><thead><tr>
        <th>Candidate</th><th>Status</th><th>Score</th><th>Started</th><th>Submitted</th></tr></thead>
        <tbody>{adminData.attempts.length ? adminData.attempts.map(a=><tr key={a.id}>
          <td><b>{a.candidate}</b><small>{a.username}</small></td>
          <td><Pill tone={a.status==='submitted'?'green':a.status==='expired'?'amber':'blue'}>{a.status.replace('_',' ')}</Pill></td>
          <td><strong>{a.status==='in_progress'?'—':a.score+'/'+a.possible}</strong></td>
          <td>{new Date(a.started_at).toLocaleString()}</td><td>{a.submitted_at?new Date(a.submitted_at).toLocaleString():'—'}</td></tr>) :
          <tr><td colSpan="5" className="table-empty">No candidate attempts yet.</td></tr>}</tbody></table></div>
      <div className="admin-tip"><Info size={17}/> Create users, edit quiz settings and manage questions in <a href="/admin/" target="_blank" rel="noreferrer">Django Admin</a>.</div>
    </section>
  </div>;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(true);
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState('overview');
  const [quiz, setQuiz] = useState(null);
  const [attempt, setAttempt] = useState(null);
  const [result, setResult] = useState(null);
  const [resultId, setResultId] = useState(null);
  const [adminData, setAdminData] = useState(null);
  const [error, setError] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [saving, setSaving] = useState(null);
  const [now, setNow] = useState(Date.now());
  const [showReview, setShowReview] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const finishingRef = useRef(false);

  async function hydrate() {
    const [a, state] = await Promise.all([api('/assessments'),api('/attempts/current')]);
    setQuiz(a.assessment);
    if (state.attempt) {
      setAttempt(state.attempt);
      setResultId(null);
      const i = state.attempt.questions.findIndex(q=>!state.attempt.answers[String(q.id)]);
      setCurrentIndex(i >= 0 ? i : 0);
      setPage('quiz');
    } else {
      setAttempt(null);
      setResultId(state.result_id || null);
      setPage('overview');
    }
  }
  useEffect(()=>{
    (async()=>{
      try {
        const s = await api('/auth/session');
        if (s.authenticated) { setUser(s.user); await hydrate(); }
      } catch (e) { setError(e.message); }
      finally { setBooting(false); }
    })();
  },[]);
  useEffect(()=>{
    if (page !== 'quiz' || !attempt) return;
    const id = setInterval(()=>setNow(Date.now()),1000);
    setNow(Date.now());
    return ()=>clearInterval(id);
  },[page,attempt?.id]);
  const timeLeft = attempt ? Math.max(0, Math.ceil((Date.parse(attempt.expires_at)-now)/1000)) : 0;
  useEffect(()=>{
    if (page==='quiz' && attempt && timeLeft<=0 && !finishingRef.current) {
      finishingRef.current=true;
      finalize(true).finally(()=>{finishingRef.current=false;});
    }
  },[page,attempt?.id,timeLeft]);

  async function signIn(username, password) {
    setBusy(true);setError('');
    try {
      const data = await api('/auth/login',{method:'POST',body:{username,password}});
      setUser(data.user);await hydrate();
    } catch(e){setError(e.message);}
    finally{setBusy(false);}
  }
  async function signOut() {
    try { await api('/auth/logout',{method:'POST'}); }
    catch(e){setError(e.message);return;}
    setUser(null);setQuiz(null);setAttempt(null);setResult(null);setResultId(null);
    setAdminData(null);setPage('overview');setError('');
  }
  async function start() {
    if (attempt) {setPage('quiz');return;}
    setBusy(true);setError('');
    try {
      const data = await api('/attempts',{method:'POST'});
      setAttempt(data.attempt);setCurrentIndex(0);setNow(Date.now());setPage('quiz');
      setResult(null);setResultId(null);
    } catch(e){
      if (e.status===409 && resultId) await viewResult();
      else {setError(e.message);setPage('instructions');}
    } finally {setBusy(false);}
  }
  async function viewResult(id = resultId) {
    setError('');
    if (!id) {setPage('result');return;}
    try {
      const data = await api('/results/'+id);
      setResult(data);setResultId(id);setShowReview(false);setPage('result');
    } catch(e){setError(e.message);}
  }
  async function onAnswer(questionId, code) {
    if (!attempt || saving !== null) return;
    const old = attempt;
    setSaving(questionId);
    setAttempt(prev=>({...prev,answers:{...prev.answers,[String(questionId)]:code}}));
    try {
      await api('/attempts/'+attempt.id+'/answers/'+questionId,{
        method:'PUT',body:{selected_code:code}
      });
    } catch(e) {
      setError(e.message);
      try {
        const updated=await api('/attempts/'+old.id);
        if (updated.attempt) setAttempt(updated.attempt);
        else if (updated.result_id) {setAttempt(null);await viewResult(updated.result_id);}
      } catch {setAttempt(old);}
    } finally {setSaving(null);}
  }
  async function finalize(auto=false) {
    if (!attempt || (saving!==null && !auto)) return;
    const unanswered=attempt.questions.length-Object.keys(attempt.answers).length;
    if (!auto && !window.confirm(unanswered
      ? 'You have '+unanswered+' unanswered questions. Submit your assessment anyway?'
      : 'Submit your assessment? You cannot change answers afterward.')) return;
    setBusy(true);setError('');
    try {
      const data = await api('/attempts/'+attempt.id+'/submit',{method:'POST'});
      setAttempt(null);
      await viewResult(data.result_id);
    } catch(e){setError(e.message);}
    finally {setBusy(false);}
  }
  async function retake() {
    setResult(null);setAttempt(null);setResultId(null);setShowReview(false);
    setPage('instructions');
  }
  async function refreshAdmin() {
    setBusy(true);setError('');
    try {const data=await api('/admin/summary');setAdminData(data);}
    catch(e){setError(e.message);}
    finally {setBusy(false);}
  }
  function navigate(id) {
    setError('');
    if(id==='quiz') {setPage(attempt?'quiz':'instructions');return;}
    if(id==='result') {viewResult();return;}
    if(id==='admin') {setPage(id);refreshAdmin();return;}
    setPage(id);
  }
  if (booting) return <div className="boot-screen"><div className="spinner"/><Brand/><p>Loading assessment portal…</p></div>;
  if (!user) return <LoginPage onLogin={signIn} busy={busy} error={error}/>;
  return <div className="app-shell">
    <Sidebar page={page} user={user} onNavigate={navigate} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen}/>
    <div className="workspace">
      <header className="topbar">
        <div className="topbar-left"><button className="mobile-menu icon-plain" aria-label="Open menu" onClick={()=>setMobileOpen(true)}><Menu/></button>
          <span className="topbar-label">{page==='quiz'?'Assessment':page==='result'?'My Result':page==='admin'?'HR Dashboard':page[0].toUpperCase()+page.slice(1)}</span></div>
        <div className="topbar-right"><span className="status-dot"/> Secure assessment
          <span className="topbar-separator"/><span className="user-avatar">{initials(user.name)}</span>
          <span className="user-name">{user.name}</span><button className="icon-plain logout" title="Sign out" aria-label="Sign out" onClick={signOut}><LogOut size={19}/></button></div>
      </header>
      <main className="content">
        {error && <div className="alert error page-error" role="alert"><Info size={18}/><span>{error}</span>
          <button className="icon-plain" onClick={()=>setError('')} aria-label="Dismiss"><X size={17}/></button></div>}
        {!quiz ? <div className="loading-card">No assessment available. Contact your assessor.</div> :
          page==='overview'?<OverviewPage quiz={quiz} onStart={start} isResuming={Boolean(attempt)} hasResult={Boolean(resultId)} onResult={()=>viewResult()}/>:
          page==='instructions'?<InstructionsPage quiz={quiz} onStart={start} isResuming={Boolean(attempt)}/>:
          page==='quiz'&&attempt?<QuizPage attempt={attempt} currentIndex={currentIndex} setCurrentIndex={setCurrentIndex}
              onAnswer={onAnswer} saving={saving} onSubmit={finalize} timeLeft={timeLeft} submitting={busy}/>:
          page==='result'?<ResultPage data={result} onOverview={()=>setPage('overview')} showReview={showReview}
              setShowReview={setShowReview} onRetake={retake}/>:
          page==='admin'&&user.is_staff?<AdminPage adminData={adminData} loading={busy} onRefresh={refreshAdmin}/>:
          <InstructionsPage quiz={quiz} onStart={start} isResuming={Boolean(attempt)}/>}
      </main>
      <footer className="footer">DBA & Data Governance Assessment <span>© {new Date().getFullYear()} · Simplicity · Velocity · Efficiency</span></footer>
    </div>
  </div>;
}
