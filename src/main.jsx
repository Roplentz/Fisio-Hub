import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Brain, Sparkles, GraduationCap, LayoutDashboard, Users, ShieldCheck, Compass, LineChart, BookOpen, Bot, Settings, Search, Bell, CheckCircle2, Activity, Rocket, ClipboardList } from 'lucide-react';
import './styles.css';

const Brand = () => (
  <div className="brand">
    <div className="logoMark"><Brain size={22}/></div>
    <div>
      <strong>FisioHub</strong>
      <span>Academy</span>
    </div>
  </div>
);

const Pill = ({children}) => <span className="pill">{children}</span>;

function LandingPage({ setPage }) {
  return (
    <main className="page landing">
      <nav className="topbar">
        <Brand />
        <div className="navlinks">
          <a>Discovery</a><a>Academy</a><a>IA Tutor</a><a>Comunidade</a>
        </div>
        <button className="btn ghost" onClick={() => setPage('student')}>Entrar</button>
      </nav>

      <section className="hero">
        <div className="heroText">
          <Pill><Sparkles size={14}/> A plataforma que evolui com sua carreira</Pill>
          <h1>A primeira Academy que conhece você antes de ensinar.</h1>
          <p>
            O FisioHub combina IA, ciência e experiência para criar uma jornada personalizada
            de desenvolvimento profissional para fisioterapeutas.
          </p>
          <div className="actions">
            <button className="btn primary" onClick={() => setPage('student')}>Ver página do aluno</button>
            <button className="btn secondary" onClick={() => setPage('admin')}>Ver admin</button>
          </div>
          <div className="trust">
            <span><CheckCircle2 size={16}/> Discovery™</span>
            <span><CheckCircle2 size={16}/> Professional Digital Twin™</span>
            <span><CheckCircle2 size={16}/> Cognitive Compass™</span>
          </div>
        </div>

        <div className="heroCard glass">
          <div className="miniHeader">
            <span>Seu próximo passo</span>
            <Compass size={20}/>
          </div>
          <h3>IA aplicada à fisioterapia</h3>
          <p>Recomendado porque seu objetivo é aumentar produtividade e criar soluções digitais.</p>
          <div className="progressBlock">
            <div className="progressTitle"><span>Trilha inicial</span><b>42%</b></div>
            <div className="progress"><i style={{width:'42%'}} /></div>
          </div>
          <div className="cardGrid">
            <div><b>3</b><span>aulas hoje</span></div>
            <div><b>1</b><span>caso clínico</span></div>
            <div><b>2</b><span>agentes IA</span></div>
          </div>
        </div>
      </section>

      <section className="features">
        {[
          ['FisioHub Discovery™', 'Onboarding conversacional para mapear objetivos, inteligências e competências.', Compass],
          ['Professional Digital Twin™', 'Um perfil vivo que acompanha a evolução profissional do usuário.', Activity],
          ['Living Curriculum™', 'Cursos vivos, atualizados por evidências e revisão científica.', BookOpen],
          ['Tutor IA', 'Um agente focado no curso, nos casos clínicos e na jornada do aluno.', Bot],
        ].map(([title, text, Icon]) => (
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

function StudentPage({ setPage }) {
  return (
    <main className="appShell">
      <aside className="sidebar">
        <Brand />
        <button className="side active"><LayoutDashboard size={18}/> Dashboard</button>
        <button className="side"><GraduationCap size={18}/> Minha trilha</button>
        <button className="side"><Compass size={18}/> Compass</button>
        <button className="side"><Bot size={18}/> Tutor IA</button>
        <button className="side"><BookOpen size={18}/> Biblioteca</button>
        <button className="side" onClick={() => setPage('landing')}>← Landing</button>
      </aside>

      <section className="workspace">
        <header className="workspaceTop">
          <div>
            <p className="eyebrow">Página do aluno</p>
            <h1>Olá, Rodrigo. Seu plano de evolução está pronto.</h1>
          </div>
          <div className="topActions"><Search/><Bell/><button className="btn primary small">Continuar aula</button></div>
        </header>

        <div className="studentGrid">
          <div className="panel wide">
            <Pill><Compass size={14}/> Cognitive Compass™</Pill>
            <h2>Melhor próximo passo</h2>
            <p>Concluir a aula “Como usar IA para criar casos clínicos” e aplicar no desafio prático.</p>
            <div className="actions"><button className="btn primary">Começar agora</button><button className="btn secondary">Ver justificativa</button></div>
          </div>

          <div className="panel">
            <h3>Professional Digital Twin™</h3>
            <div className="radarMock">
              <span>IA 82%</span><span>Clínica 76%</span><span>Pesquisa 61%</span><span>Gestão 54%</span>
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
              <div><b>Pontos fortes</b><p>Ciência, inovação, visão sistêmica.</p></div>
              <div><b>Próximos desenvolvimentos</b><p>Automação, produto e funil comercial.</p></div>
              <div><b>Oportunidades</b><p>Curso IA, agentes clínicos, comunidade.</p></div>
              <div><b>Pontos de atenção</b><p>Priorizar MVP antes de ampliar módulos.</p></div>
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
      <aside className="sidebar dark">
        <Brand />
        <button className="side active"><LayoutDashboard size={18}/> Visão geral</button>
        <button className="side"><Users size={18}/> Alunos</button>
        <button className="side"><GraduationCap size={18}/> Cursos</button>
        <button className="side"><Bot size={18}/> Agentes</button>
        <button className="side"><LineChart size={18}/> Analytics</button>
        <button className="side"><ShieldCheck size={18}/> Governança</button>
        <button className="side" onClick={() => setPage('landing')}>← Landing</button>
      </aside>

      <section className="workspace">
        <header className="workspaceTop">
          <div>
            <p className="eyebrow">Painel administrativo</p>
            <h1>Controle do MVP FisioHub Academy</h1>
          </div>
          <button className="btn primary small"><Settings size={16}/> Configurar</button>
        </header>

        <div className="metrics">
          <div><b>128</b><span>alunos beta</span></div>
          <div><b>74%</b><span>Discovery concluído</span></div>
          <div><b>42%</b><span>progresso médio</span></div>
          <div><b>91%</b><span>satisfação inicial</span></div>
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
