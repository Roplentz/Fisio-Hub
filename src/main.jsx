import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Brain, Sparkles, GraduationCap, LayoutDashboard, Users, ShieldCheck, Compass, LineChart, BookOpen, Bot, Settings, Search, Bell, CheckCircle2, Activity, Rocket, ClipboardList, ArrowRight } from 'lucide-react';
import { adminMetrics, canvas, intelligenceMap, studentStats } from './product-data.js';
import './styles.css';

const Brand = () => (
  <div className="brand">
    <div className="logoMark"><Brain size={22}/></div>
    <div>
      <strong>FisioHub</strong>
      <span>Academy MVP</span>
    </div>
  </div>
);

const Pill = ({children}) => <span className="pill">{children}</span>;
const MetricCard = ({value, label}) => <div><b>{value}</b><span>{label}</span></div>;

function LandingPage({ setPage }) {
  const features = [
    ['FisioHub Discovery™', 'Onboarding conversacional para mapear objetivos, inteligências e competências.', Compass],
    ['Professional Digital Twin™', 'Um perfil vivo que acompanha a evolução profissional do usuário.', Activity],
    ['Living Curriculum™', 'Cursos vivos, atualizados por evidências e revisão científica.', BookOpen],
    ['Tutor IA', 'Um agente focado no curso, nos casos clínicos e na jornada do aluno.', Bot],
  ];

  return (
    <main className="page landing">
      <nav className="topbar">
        <Brand />
        <div className="navlinks">
          <a>Discovery</a><a>Academy</a><a>Tutor IA</a><a>Admin</a>
        </div>
        <button className="btn ghost" onClick={() => setPage('student')}>Entrar</button>
      </nav>

      <section className="hero">
        <div className="heroText">
          <Pill><Sparkles size={14}/> MVP FisioHub Academy</Pill>
          <h1>A Academy que conhece você antes de ensinar.</h1>
          <p>
            Uma experiência inicial para validar o FisioHub: Discovery™, Professional Digital Twin™,
            Cognitive Compass™, trilha de IA e Tutor IA em uma jornada simples para fisioterapeutas.
          </p>
          <div className="actions">
            <button className="btn primary" onClick={() => setPage('student')}>Ver página do aluno <ArrowRight size={17}/></button>
            <button className="btn secondary" onClick={() => setPage('admin')}>Ver admin</button>
          </div>
          <div className="trust">
            <span><CheckCircle2 size={16}/> Complexidade invisível</span>
            <span><CheckCircle2 size={16}/> Ciência + IA</span>
            <span><CheckCircle2 size={16}/> Evolução profissional</span>
          </div>
        </div>

        <div className="heroCard glass">
          <div className="miniHeader">
            <span>Seu próximo passo</span>
            <Compass size={20}/>
          </div>
          <h3>IA aplicada à fisioterapia</h3>
          <p>Recomendado porque seu objetivo é aumentar produtividade, criar aulas melhores e usar IA com segurança.</p>
          <div className="progressBlock">
            <div className="progressTitle"><span>Trilha inicial</span><b>42%</b></div>
            <div className="progress"><i style={{width:'42%'}} /></div>
          </div>
          <div className="cardGrid">
            {studentStats.slice(1).map((item) => <MetricCard key={item.label} {...item}/>) }
          </div>
        </div>
      </section>

      <section className="features">
        {features.map(([title, text, Icon]) => (
          <div className="feature" key={title}>
            <Icon size={24}/>
            <h3>{title}</h3>
            <p>{text}</p>
          </div>
        ))}
      </section>
    </main>
  )
}

function Sidebar({ mode, setPage }) {
  return (
    <aside className={`sidebar ${mode === 'admin' ? 'dark' : ''}`}>
      <Brand />
      <button className="side active"><LayoutDashboard size={18}/> Dashboard</button>
      <button className="side"><GraduationCap size={18}/> Trilhas</button>
      <button className="side"><Compass size={18}/> Compass</button>
      <button className="side"><Bot size={18}/> Agentes</button>
      <button className="side"><BookOpen size={18}/> Conteúdos</button>
      <button className="side" onClick={() => setPage('landing')}>← Landing</button>
    </aside>
  )
}

function StudentPage({ setPage }) {
  return (
    <main className="appShell">
      <Sidebar setPage={setPage}/>
      <section className="workspace">
        <header className="workspaceTop">
          <div>
            <p className="eyebrow">Página do aluno</p>
            <h1>Olá, Rodrigo. Seu plano de evolução está pronto.</h1>
          </div>
          <div className="topActions"><Search/><Bell/><button className="btn primary small">Continuar aula</button></div>
        </header>

        <div className="studentGrid">
          <div className="panel wide highlight">
            <Pill><Compass size={14}/> Cognitive Compass™</Pill>
            <h2>Melhor próximo passo</h2>
            <p>Concluir a aula “Como usar IA para criar casos clínicos” e aplicar no desafio prático.</p>
            <div className="actions"><button className="btn primary">Começar agora</button><button className="btn secondary">Ver justificativa</button></div>
          </div>

          <div className="panel">
            <h3>Professional Digital Twin™</h3>
            <div className="radarMock">
              {intelligenceMap.map((item) => <span key={item.label}>{item.label} {item.value}</span>)}
            </div>
          </div>

          <div className="panel">
            <h3>Trilha IA para Fisioterapeutas</h3>
            <div className="progressBlock">
              <div className="progressTitle"><span>Progresso</span><b>42%</b></div>
              <div className="progress"><i style={{width:'42%'}} /></div>
            </div>
            <p>Próxima aula: Prompt clínico seguro.</p>
          </div>

          <div className="panel wide">
            <h3>Professional Evolution Canvas™</h3>
            <div className="canvasGrid">
              {canvas.map((item) => <div key={item.title}><b>{item.title}</b><p>{item.text}</p></div>)}
            </div>
          </div>

          <div className="panel">
            <h3>Tutor IA</h3>
            <p>“Quer transformar sua próxima aula em um caso clínico interativo?”</p>
            <button className="btn secondary">Conversar</button>
          </div>
        </div>
      </section>
    </main>
  )
}

function AdminPage({ setPage }) {
  return (
    <main className="appShell admin">
      <Sidebar mode="admin" setPage={setPage}/>
      <section className="workspace">
        <header className="workspaceTop">
          <div>
            <p className="eyebrow">Painel administrativo</p>
            <h1>Controle do MVP FisioHub Academy</h1>
          </div>
          <button className="btn primary small"><Settings size={16}/> Configurar</button>
        </header>

        <div className="metrics">
          {adminMetrics.map((item) => <MetricCard key={item.label} {...item}/>) }
        </div>

        <div className="studentGrid">
          <div className="panel wide">
            <h3>Pipeline do aluno</h3>
            <div className="pipeline">
              {['Cadastro','Discovery','Twin inicial','Trilha','Tutor IA','Certificado'].map((x,i)=><span key={x} className={i<4?'done':''}>{x}</span>)}
            </div>
          </div>

          <div className="panel">
            <h3>Curso ativo</h3>
            <p><b>IA para Fisioterapeutas</b></p>
            <p>12 aulas · 4 casos clínicos · 1 certificado</p>
          </div>

          <div className="panel">
            <h3>Agentes ativos</h3>
            <p>Tutor IA, Professor IA, Revisor Científico.</p>
            <button className="btn secondary">Ver catálogo</button>
          </div>

          <div className="panel wide">
            <h3>Living Curriculum™</h3>
            <div className="list">
              <p><ClipboardList size={16}/> 3 conteúdos aguardando revisão científica</p>
              <p><Rocket size={16}/> 2 melhorias pedagógicas sugeridas pela IA</p>
              <p><ShieldCheck size={16}/> 0 alertas críticos de governança</p>
            </div>
          </div>

          <div className="panel">
            <h3>Próxima decisão</h3>
            <p>Validar se os alunos usam o Tutor IA semanalmente antes de liberar comunidade.</p>
          </div>
        </div>
      </section>
    </main>
  )
}

function App() {
  const [page, setPage] = useState('landing');
  if (page === 'student') return <StudentPage setPage={setPage}/>;
  if (page === 'admin') return <AdminPage setPage={setPage}/>;
  return <LandingPage setPage={setPage}/>;
}

createRoot(document.getElementById('root')).render(<App />);
