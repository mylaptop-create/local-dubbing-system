import React, { useState, useEffect } from 'react';
import {
  Video,
  Play,
  FileText,
  Activity,
  HardDrive,
  List,
  PlusCircle,
  RotateCcw,
  Trash2,
  Download,
  CheckCircle2,
  Cpu,
  ArrowRight,
  ShieldCheck,
  Globe,
  Link,
  UploadCloud
} from 'lucide-react';
import type { Project, SystemDiagnostics, Voice, StorageInfo, LogEntry } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'new' | 'projects' | 'queue' | 'diagnostics' | 'storage' | 'logs'>('new');
  const [inputSourceMode, setInputSourceMode] = useState<'file' | 'url'>('file');
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [storage, setStorage] = useState<StorageInfo | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Form State
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [projectName, setProjectName] = useState('');
  const [ttsVoice, setTtsVoice] = useState('en-US-JennyNeural');
  const [audioMode, setAudioMode] = useState<'replace' | 'duck'>('replace');
  const [burnSubtitles, setBurnSubtitles] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchDiagnostics();
    fetchVoices();
    fetchProjects();
    fetchStorage();
    fetchLogs();
    const interval = setInterval(() => {
      fetchProjects();
      fetchLogs();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const fetchDiagnostics = async () => {
    try {
      const res = await fetch('/api/diagnostics');
      if (res.ok) setDiagnostics(await res.json());
    } catch (e) {}
  };

  const fetchVoices = async () => {
    try {
      const res = await fetch('/api/voices');
      if (res.ok) setVoices(await res.json());
    } catch (e) {}
  };

  const fetchProjects = async () => {
    try {
      const res = await fetch('/api/projects');
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        if (selectedProject) {
          const updated = data.find((p: Project) => p.id === selectedProject.id);
          if (updated) setSelectedProject(updated);
        }
      }
    } catch (e) {}
  };

  const fetchStorage = async () => {
    try {
      const res = await fetch('/api/storage');
      if (res.ok) setStorage(await res.json());
    } catch (e) {}
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs');
      if (res.ok) setLogs(await res.json());
    } catch (e) {}
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName) return;
    setIsSubmitting(true);

    try {
      let createdProject: Project;
      if (inputSourceMode === 'file') {
        if (!videoFile) return;
        const formData = new FormData();
        formData.append('video', videoFile);
        formData.append('name', projectName);
        formData.append('source_lang', 'zh');
        formData.append('target_lang', 'en');
        formData.append('tts_voice', ttsVoice);
        formData.append('audio_mode', audioMode);
        formData.append('burn_subtitles', String(burnSubtitles));

        const res = await fetch('/api/projects', {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) throw new Error("Failed to upload file project");
        createdProject = await res.json();
      } else {
        if (!videoUrl) return;
        const res = await fetch('/api/projects/from-url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: videoUrl,
            name: projectName,
            source_lang: 'zh',
            target_lang: 'en',
            tts_voice: ttsVoice,
            audio_mode: audioMode,
            burn_subtitles: burnSubtitles
          }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Failed to download video from URL");
        }
        createdProject = await res.json();
      }

      await fetch(`/api/projects/${createdProject.id}/start`, { method: 'POST' });
      setVideoFile(null);
      setVideoUrl('');
      setProjectName('');
      await fetchProjects();
      setSelectedProject(createdProject);
      setActiveTab('queue');
    } catch (e: any) {
      alert(`Error creating project: ${e.message}`);
    } fontally: {
      setIsSubmitting(false);
    }
  };

  const handleResume = async (projectId: string) => {
    await fetch(`/api/projects/${projectId}/resume`, { method: 'POST' });
    fetchProjects();
  };

  const handleDelete = async (projectId: string) => {
    if (confirm('Are you sure you want to delete this project?')) {
      await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
      if (selectedProject?.id === projectId) setSelectedProject(null);
      fetchProjects();
    }
  };

  const handleCleanTemp = async () => {
    await fetch('/api/storage/clean-temp', { method: 'POST' });
    fetchStorage();
  };

  return (
    <div className="min-h-screen bg-[#e8ebe6] text-[#0e0f0c] font-sans flex flex-col">
      {/* Top Wise Brand Navigation Bar */}
      <header className="bg-white border-b border-[#0e0f0c]/10 sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-[#9fe870] text-[#0e0f0c] p-2.5 rounded-[24px] font-black text-xl flex items-center justify-center shadow-sm">
              <Globe className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <span className="font-wise-hero text-2xl tracking-tight text-[#0e0f0c]">Wise Dubbing</span>
              <span className="ml-2 bg-[#e2f6d5] text-[#163300] text-xs font-semibold px-2.5 py-0.5 rounded-full border border-[#c5edab]">
                Local AI Studio
              </span>
            </div>
          </div>

          <nav className="flex items-center space-x-2">
            <button
              onClick={() => setActiveTab('new')}
              className={`px-5 py-2.5 rounded-[24px] text-sm font-semibold transition-all cursor-pointer ${
                activeTab === 'new'
                  ? 'bg-[#9fe870] text-[#0e0f0c] shadow-sm'
                  : 'text-[#454745] hover:bg-[#e8ebe6] hover:text-[#0e0f0c]'
              }`}
            >
              <PlusCircle className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              New Translation
            </button>

            <button
              onClick={() => setActiveTab('projects')}
              className={`px-5 py-2.5 rounded-[24px] text-sm font-semibold transition-all cursor-pointer ${
                activeTab === 'projects'
                  ? 'bg-[#9fe870] text-[#0e0f0c] shadow-sm'
                  : 'text-[#454745] hover:bg-[#e8ebe6] hover:text-[#0e0f0c]'
              }`}
            >
              <List className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              Projects ({projects.length})
            </button>

            <button
              onClick={() => setActiveTab('queue')}
              className={`px-5 py-2.5 rounded-[24px] text-sm font-semibold transition-all cursor-pointer ${
                activeTab === 'queue'
                  ? 'bg-[#9fe870] text-[#0e0f0c] shadow-sm'
                  : 'text-[#454745] hover:bg-[#e8ebe6] hover:text-[#0e0f0c]'
              }`}
            >
              <Activity className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              Pipeline Queue
            </button>

            <button
              onClick={() => setActiveTab('diagnostics')}
              className={`px-5 py-2.5 rounded-[24px] text-sm font-semibold transition-all cursor-pointer ${
                activeTab === 'diagnostics'
                  ? 'bg-[#9fe870] text-[#0e0f0c] shadow-sm'
                  : 'text-[#454745] hover:bg-[#e8ebe6] hover:text-[#0e0f0c]'
              }`}
            >
              <Cpu className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              System Health
            </button>

            <button
              onClick={() => setActiveTab('storage')}
              className={`px-5 py-2.5 rounded-[24px] text-sm font-semibold transition-all cursor-pointer ${
                activeTab === 'storage'
                  ? 'bg-[#9fe870] text-[#0e0f0c] shadow-sm'
                  : 'text-[#454745] hover:bg-[#e8ebe6] hover:text-[#0e0f0c]'
              }`}
            >
              <HardDrive className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              Storage
            </button>

            <button
              onClick={() => setActiveTab('logs')}
              className={`px-5 py-2.5 rounded-[24px] text-sm font-semibold transition-all cursor-pointer ${
                activeTab === 'logs'
                  ? 'bg-[#9fe870] text-[#0e0f0c] shadow-sm'
                  : 'text-[#454745] hover:bg-[#e8ebe6] hover:text-[#0e0f0c]'
              }`}
            >
              <FileText className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              Logs
            </button>
          </nav>
        </div>
      </header>

      {/* Hero Header Banner */}
      <section className="bg-[#e8ebe6] py-8 px-6 border-b border-[#0e0f0c]/5">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="font-wise-hero text-4xl md:text-5xl tracking-tight text-[#0e0f0c]">
              Chinese Video → English Dubbing.
            </h1>
            <p className="text-[#454745] text-base md:text-lg mt-2 max-w-2xl font-normal">
              Zero complexity. Local inference, automatic timing alignment, speech synthesis, and subtitle generation.
            </p>
          </div>

          {diagnostics && (
            <div className="bg-white p-4 rounded-[24px] border border-[#0e0f0c] flex items-center space-x-4 shadow-sm">
              <div className="w-3 h-3 rounded-full bg-[#2ead4b] animate-pulse" />
              <div className="text-xs">
                <div className="font-bold text-[#0e0f0c]">
                  Hardware: {diagnostics.gpu.available ? diagnostics.gpu.name : 'CPU Fallback'}
                </div>
                <div className="text-[#868685] mt-0.5">
                  RAM: {diagnostics.ram_available_gb} GB Free · FFmpeg: {diagnostics.ffmpeg.available ? 'Ready' : 'Missing'}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Main Surface Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        {/* NEW TRANSLATION TAB */}
        {activeTab === 'new' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Signature Converter-style Card Widget */}
            <div className="lg:col-span-7 bg-white p-8 rounded-[24px] border border-[#0e0f0c] shadow-md space-y-6">
              <div className="flex items-center justify-between border-b border-[#0e0f0c]/10 pb-4">
                <h2 className="font-wise-hero text-2xl text-[#0e0f0c]">Create Translation Task</h2>
                <div className="flex items-center bg-[#e8ebe6] p-1 rounded-[24px] border border-[#0e0f0c]/10 text-xs font-bold">
                  <button
                    type="button"
                    onClick={() => setInputSourceMode('file')}
                    className={`px-3 py-1.5 rounded-[20px] cursor-pointer transition-all ${
                      inputSourceMode === 'file' ? 'bg-[#9fe870] text-[#0e0f0c]' : 'text-[#454745]'
                    }`}
                  >
                    <UploadCloud className="w-3.5 h-3.5 inline mr-1" /> File Upload
                  </button>
                  <button
                    type="button"
                    onClick={() => setInputSourceMode('url')}
                    className={`px-3 py-1.5 rounded-[20px] cursor-pointer transition-all ${
                      inputSourceMode === 'url' ? 'bg-[#9fe870] text-[#0e0f0c]' : 'text-[#454745]'
                    }`}
                  >
                    <Link className="w-3.5 h-3.5 inline mr-1" /> YouTube / Bilibili Link
                  </button>
                </div>
              </div>

              <form onSubmit={handleCreateProject} className="space-y-6">
                {/* File Upload Box OR URL Input Box */}
                {inputSourceMode === 'file' ? (
                  <div className="bg-[#e8ebe6] border-2 border-dashed border-[#0e0f0c]/20 hover:border-[#0e0f0c] p-6 rounded-[24px] text-center transition-all cursor-pointer">
                    <input
                      type="file"
                      accept="video/*"
                      onChange={(e) => {
                        if (e.target.files?.[0]) {
                          setVideoFile(e.target.files[0]);
                          if (!projectName) setProjectName(e.target.files[0].name.replace(/\.[^/.]+$/, ''));
                        }
                      }}
                      className="hidden"
                      id="video-upload"
                    />
                    <label htmlFor="video-upload" className="cursor-pointer block">
                      <Video className="w-10 h-10 mx-auto text-[#0e0f0c] mb-2" />
                      {videoFile ? (
                        <p className="text-[#054d28] font-bold text-sm bg-[#e2f6d5] py-2 px-4 rounded-full inline-block border border-[#c5edab]">
                          ✓ {videoFile.name} ({(videoFile.size / (1024 * 1024)).toFixed(1)} MB)
                        </p>
                      ) : (
                        <div>
                          <p className="text-[#0e0f0c] font-semibold text-base">Select or drop Chinese video file</p>
                          <p className="text-[#868685] text-xs mt-1">MP4, MOV, MKV or AVI supported</p>
                        </div>
                      )}
                    </label>
                  </div>
                ) : (
                  <div className="bg-[#e8ebe6] p-6 rounded-[24px] border border-[#0e0f0c]/10 space-y-3">
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#454745]">
                      YouTube or Bilibili Video URL
                    </label>
                    <div className="flex items-center space-x-2">
                      <Link className="w-5 h-5 text-[#868685]" />
                      <input
                        type="url"
                        value={videoUrl}
                        onChange={(e) => setVideoUrl(e.target.value)}
                        placeholder="https://www.youtube.com/watch?v=... or https://www.bilibili.com/video/BV..."
                        required={inputSourceMode === 'url'}
                        className="w-full bg-white border border-[#0e0f0c] rounded-[12px] px-4 py-2.5 text-[#0e0f0c] font-medium text-sm focus:outline-none focus:ring-2 focus:ring-[#9fe870]"
                      />
                    </div>
                    <p className="text-xs text-[#868685]">
                      Directly downloads video audio stream and creates translation project.
                    </p>
                  </div>
                )}

                {/* Project Name */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#454745] mb-1.5">
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="e.g. Course 01 - Lesson Intro"
                    required
                    className="w-full bg-[#e8ebe6] border border-[#0e0f0c] rounded-[12px] px-4 py-3 text-[#0e0f0c] font-medium text-sm focus:outline-none focus:ring-2 focus:ring-[#9fe870]"
                  />
                </div>

                {/* Conversion Settings Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#454745] mb-1.5">
                      English Voice
                    </label>
                    <select
                      value={ttsVoice}
                      onChange={(e) => setTtsVoice(e.target.value)}
                      className="w-full bg-[#e8ebe6] border border-[#0e0f0c] rounded-[12px] px-3 py-3 text-[#0e0f0c] text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#9fe870]"
                    >
                      {voices.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.name} ({v.gender})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#454745] mb-1.5">
                      Audio Mixing Strategy
                    </label>
                    <select
                      value={audioMode}
                      onChange={(e) => setAudioMode(e.target.value as any)}
                      className="w-full bg-[#e8ebe6] border border-[#0e0f0c] rounded-[12px] px-3 py-3 text-[#0e0f0c] text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#9fe870]"
                    >
                      <option value="replace">Replace original audio completely</option>
                      <option value="duck">Duck background audio (Keep subtle original voice)</option>
                    </select>
                  </div>
                </div>

                {/* Subtitle Checkbox */}
                <div className="flex items-center space-x-3 bg-[#e8ebe6] p-4 rounded-[16px] border border-[#0e0f0c]/10">
                  <input
                    type="checkbox"
                    id="burn-sub"
                    checked={burnSubtitles}
                    onChange={(e) => setBurnSubtitles(e.target.checked)}
                    className="w-5 h-5 rounded text-[#0e0f0c] focus:ring-[#9fe870] accent-[#9fe870]"
                  />
                  <label htmlFor="burn-sub" className="text-sm text-[#0e0f0c] font-medium cursor-pointer">
                    Burn English subtitles permanently into video frame
                  </label>
                </div>

                {/* Signature Wise Green CTA Button */}
                <button
                  type="submit"
                  disabled={(inputSourceMode === 'file' && !videoFile) || (inputSourceMode === 'url' && !videoUrl) || isSubmitting}
                  className="w-full bg-[#9fe870] hover:bg-[#cdffad] active:bg-[#c5edab] disabled:opacity-50 text-[#0e0f0c] font-wise-hero text-lg py-4 rounded-[24px] transition-all cursor-pointer flex items-center justify-center space-x-2 shadow-sm border border-[#0e0f0c]"
                >
                  <Play className="w-5 h-5 fill-current" />
                  <span>{isSubmitting ? 'Initializing Project...' : 'Start Dubbing Project'}</span>
                  <ArrowRight className="w-5 h-5" />
                </button>
              </form>
            </div>

            {/* Side Feature Highlights Card */}
            <div className="lg:col-span-5 space-y-4">
              <div className="bg-[#0e0f0c] text-[#9fe870] p-8 rounded-[24px] space-y-4 shadow-md">
                <h3 className="font-wise-hero text-2xl text-white">How Wise Dubbing Works</h3>
                <div className="space-y-4 text-sm text-[#e8ebe6]">
                  <div className="flex items-start space-x-3">
                    <div className="p-1.5 bg-[#9fe870] text-[#0e0f0c] rounded-full font-bold text-xs mt-0.5">1</div>
                    <p><strong className="text-white">Speech Recognition:</strong> FasterWhisper transcribes Chinese speech into precise timestamped segments.</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="p-1.5 bg-[#9fe870] text-[#0e0f0c] rounded-full font-bold text-xs mt-0.5">2</div>
                    <p><strong className="text-white">Neural Translation:</strong> Translates Chinese text to clear English while preserving timestamps.</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="p-1.5 bg-[#9fe870] text-[#0e0f0c] rounded-full font-bold text-xs mt-0.5">3</div>
                    <p><strong className="text-white">Speech Assembly:</strong> Generates English speech and aligns tempo to original video clips.</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-[24px] border border-[#0e0f0c] space-y-3">
                <div className="flex items-center space-x-2 text-[#054d28]">
                  <ShieldCheck className="w-5 h-5" />
                  <span className="font-bold text-sm">100% Local Execution</span>
                </div>
                <p className="text-xs text-[#454745] leading-relaxed">
                  Your video files never leave your computer. Processing, database state, and intermediate files are handled entirely on your machine.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* MY PROJECTS TAB */}
        {activeTab === 'projects' && (
          <div className="space-y-6">
            <h2 className="font-wise-hero text-3xl text-[#0e0f0c]">My Projects</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((p) => (
                <div key={p.id} className="bg-white border border-[#0e0f0c] p-6 rounded-[24px] space-y-4 shadow-sm flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-wise-hero text-xl text-[#0e0f0c] truncate">{p.name}</h3>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold border ${
                          p.status === 'COMPLETED'
                            ? 'bg-[#e2f6d5] text-[#054d28] border-[#c5edab]'
                            : p.status === 'FAILED'
                            ? 'bg-[#320707] text-white border-[#a72027]'
                            : 'bg-[#ffd11a] text-[#4a3b1c] border-[#b86700]'
                        }`}
                      >
                        {p.status}
                      </span>
                    </div>
                    <p className="text-xs text-[#868685] font-mono">ID: {p.id}</p>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold text-[#454745]">
                      <span>Stage: {p.current_stage}</span>
                      <span>{p.progress_pct.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-[#e8ebe6] rounded-full h-2 overflow-hidden border border-[#0e0f0c]/10">
                      <div className="bg-[#9fe870] h-full transition-all duration-300" style={{ width: `${p.progress_pct}%` }} />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-[#0e0f0c]/10">
                    <button
                      onClick={() => {
                        setSelectedProject(p);
                        setActiveTab('queue');
                      }}
                      className="text-[#0e0f0c] font-bold text-xs hover:underline flex items-center space-x-1 cursor-pointer"
                    >
                      <span>View Pipeline & Downloads</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                    <div className="flex space-x-1">
                      {p.status === 'FAILED' && (
                        <button
                          onClick={() => handleResume(p.id)}
                          className="p-2 text-[#0e0f0c] hover:bg-[#e8ebe6] rounded-full cursor-pointer"
                          title="Resume"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="p-2 text-[#d03238] hover:bg-[#e8ebe6] rounded-full cursor-pointer"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* PROCESSING QUEUE / DETAILS TAB */}
        {activeTab === 'queue' && (
          <div className="space-y-6">
            <h2 className="font-wise-hero text-3xl text-[#0e0f0c]">Pipeline Inspector</h2>

            {selectedProject ? (
              <div className="bg-white border border-[#0e0f0c] rounded-[24px] p-8 space-y-6 shadow-sm">
                <div className="flex justify-between items-center border-b border-[#0e0f0c]/10 pb-4">
                  <div>
                    <h3 className="font-wise-hero text-2xl text-[#0e0f0c]">{selectedProject.name}</h3>
                    <p className="text-xs text-[#868685]">ID: {selectedProject.id}</p>
                  </div>
                  {selectedProject.status === 'FAILED' && (
                    <button
                      onClick={() => handleResume(selectedProject.id)}
                      className="bg-[#ffd11a] text-[#4a3b1c] hover:bg-[#b86700] hover:text-white px-4 py-2 rounded-[24px] text-xs font-bold border border-[#0e0f0c] flex items-center space-x-2 cursor-pointer"
                    >
                      <RotateCcw className="w-4 h-4" />
                      <span>Resume Stage</span>
                    </button>
                  )}
                </div>

                {/* Progress bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm font-bold text-[#0e0f0c]">
                    <span>Current Stage: {selectedProject.current_stage}</span>
                    <span>{selectedProject.progress_pct.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-[#e8ebe6] rounded-full h-3 overflow-hidden border border-[#0e0f0c]/20">
                    <div
                      className="bg-[#9fe870] h-full transition-all duration-500"
                      style={{ width: `${selectedProject.progress_pct}%` }}
                    />
                  </div>
                </div>

                {/* Outputs section if completed */}
                {selectedProject.status === 'COMPLETED' && (
                  <div className="bg-[#e2f6d5] border border-[#c5edab] p-6 rounded-[24px] space-y-4">
                    <h4 className="font-wise-hero text-lg text-[#054d28] flex items-center space-x-2">
                      <CheckCircle2 className="w-5 h-5" />
                      <span>Download Intermediate & Final Artifacts</span>
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <a
                        href={`/api/projects/${selectedProject.id}/files/final_english_video.mp4`}
                        download
                        className="bg-white hover:bg-[#e8ebe6] p-3 rounded-[12px] border border-[#0e0f0c] flex items-center justify-between text-[#0e0f0c] font-semibold"
                      >
                        <span>final_english_video.mp4</span>
                        <Download className="w-4 h-4 text-[#0e0f0c]" />
                      </a>
                      <a
                        href={`/api/projects/${selectedProject.id}/files/english_subtitles.srt`}
                        download
                        className="bg-white hover:bg-[#e8ebe6] p-3 rounded-[12px] border border-[#0e0f0c] flex items-center justify-between text-[#0e0f0c] font-semibold"
                      >
                        <span>english_subtitles.srt</span>
                        <Download className="w-4 h-4 text-[#0e0f0c]" />
                      </a>
                      <a
                        href={`/api/projects/${selectedProject.id}/files/chinese_transcript.srt`}
                        download
                        className="bg-white hover:bg-[#e8ebe6] p-3 rounded-[12px] border border-[#0e0f0c] flex items-center justify-between text-[#0e0f0c] font-semibold"
                      >
                        <span>chinese_transcript.srt</span>
                        <Download className="w-4 h-4 text-[#0e0f0c]" />
                      </a>
                      <a
                        href={`/api/projects/${selectedProject.id}/files/generated_english_audio.wav`}
                        download
                        className="bg-white hover:bg-[#e8ebe6] p-3 rounded-[12px] border border-[#0e0f0c] flex items-center justify-between text-[#0e0f0c] font-semibold"
                      >
                        <span>generated_english_audio.wav</span>
                        <Download className="w-4 h-4 text-[#0e0f0c]" />
                      </a>
                    </div>
                  </div>
                )}

                {/* Segments Preview */}
                {selectedProject.segments && selectedProject.segments.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-wise-hero text-lg text-[#0e0f0c]">Transcript & Alignment Segments</h4>
                    <div className="max-h-72 overflow-y-auto space-y-2 border border-[#0e0f0c]/10 p-4 rounded-[16px] bg-[#e8ebe6]">
                      {selectedProject.segments.map((seg) => (
                        <div key={seg.id} className="text-xs p-3 rounded-[12px] bg-white border border-[#0e0f0c]/10 space-y-1">
                          <div className="text-[#0e0f0c] font-mono font-bold">
                            [{seg.start.toFixed(2)}s → {seg.end.toFixed(2)}s]
                          </div>
                          <div className="text-[#454745]"><strong>ZH:</strong> {seg.text}</div>
                          {seg.translated_text && <div className="text-[#054d28] font-medium"><strong>EN:</strong> {seg.translated_text}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-[#868685] font-medium">Select a project from "My Projects" to inspect progress and download files.</p>
            )}
          </div>
        )}

        {/* SYSTEM HEALTH TAB */}
        {activeTab === 'diagnostics' && diagnostics && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h2 className="font-wise-hero text-3xl text-[#0e0f0c]">System Health & Hardware</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white border border-[#0e0f0c] p-6 rounded-[24px] space-y-2 shadow-sm">
                <h3 className="text-[#868685] text-xs font-bold uppercase tracking-wider">Operating System</h3>
                <p className="text-2xl font-wise-hero text-[#0e0f0c]">{diagnostics.os}</p>
                <p className="text-xs text-[#454745] font-medium">{diagnostics.platform}</p>
              </div>

              <div className="bg-white border border-[#0e0f0c] p-6 rounded-[24px] space-y-2 shadow-sm">
                <h3 className="text-[#868685] text-xs font-bold uppercase tracking-wider">GPU Acceleration</h3>
                <p className="text-2xl font-wise-hero text-[#054d28]">
                  {diagnostics.gpu.available ? diagnostics.gpu.name : 'CPU Fallback Mode'}
                </p>
                <p className="text-xs text-[#454745] font-medium">
                  {diagnostics.gpu.available ? `VRAM: ${diagnostics.gpu.vram_gb} GB` : 'No CUDA GPU detected; processing on CPU'}
                </p>
              </div>

              <div className="bg-white border border-[#0e0f0c] p-6 rounded-[24px] space-y-2 shadow-sm">
                <h3 className="text-[#868685] text-xs font-bold uppercase tracking-wider">System RAM</h3>
                <p className="text-2xl font-wise-hero text-[#0e0f0c]">{diagnostics.ram_available_gb} GB Free</p>
                <p className="text-xs text-[#454745] font-medium">Total Installed RAM: {diagnostics.ram_total_gb} GB</p>
              </div>

              <div className="bg-white border border-[#0e0f0c] p-6 rounded-[24px] space-y-2 shadow-sm">
                <h3 className="text-[#868685] text-xs font-bold uppercase tracking-wider">FFmpeg Engine</h3>
                <p className="text-2xl font-wise-hero text-[#0e0f0c]">{diagnostics.ffmpeg.available ? 'Ready' : 'Not Found'}</p>
                <p className="text-xs text-[#454745] truncate font-mono">{diagnostics.ffmpeg.path || 'N/A'}</p>
              </div>
            </div>
          </div>
        )}

        {/* STORAGE TAB */}
        {activeTab === 'storage' && storage && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="font-wise-hero text-3xl text-[#0e0f0c]">Storage Usage</h2>
              <button
                onClick={handleCleanTemp}
                className="bg-[#0e0f0c] hover:bg-[#454745] text-white px-5 py-2.5 rounded-[24px] text-xs font-bold cursor-pointer"
              >
                Clean Temporary Cache
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white border border-[#0e0f0c] p-6 rounded-[24px] space-y-1 shadow-sm">
                <div className="text-[#868685] text-xs font-bold uppercase tracking-wider">Projects Storage</div>
                <div className="text-3xl font-wise-hero text-[#0e0f0c]">{storage.projects_size_mb} MB</div>
              </div>
              <div className="bg-white border border-[#0e0f0c] p-6 rounded-[24px] space-y-1 shadow-sm">
                <div className="text-[#868685] text-xs font-bold uppercase tracking-wider">Model Cache</div>
                <div className="text-3xl font-wise-hero text-[#0e0f0c]">{storage.models_size_mb} MB</div>
              </div>
              <div className="bg-white border border-[#0e0f0c] p-6 rounded-[24px] space-y-1 shadow-sm">
                <div className="text-[#868685] text-xs font-bold uppercase tracking-wider">Free Disk Space</div>
                <div className="text-3xl font-wise-hero text-[#054d28]">{storage.disk_free_gb} GB</div>
              </div>
            </div>
          </div>
        )}

        {/* LOGS TAB */}
        {activeTab === 'logs' && (
          <div className="space-y-4">
            <h2 className="font-wise-hero text-3xl text-[#0e0f0c]">System Logs</h2>
            <div className="bg-[#0e0f0c] text-[#e8ebe6] p-6 rounded-[24px] font-mono text-xs max-h-96 overflow-y-auto space-y-2 border border-[#0e0f0c]">
              {logs.map((l) => (
                <div key={l.id} className="pb-1 border-b border-[#454745]/20">
                  <span className="text-[#868685]">[{l.created_at}]</span>{' '}
                  <span className={l.level === 'ERROR' ? 'text-[#d03238] font-bold' : 'text-[#9fe870] font-bold'}>
                    [{l.level}]
                  </span>{' '}
                  {l.stage && <span className="text-[#ffd11a]">[{l.stage}]</span>} {l.message}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Wise Style Footer */}
      <footer className="bg-[#0e0f0c] text-[#e8ebe6] py-8 px-6 border-t border-[#0e0f0c] mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center text-xs text-[#868685]">
          <div>Wise VideoDub Studio · Local-first Chinese to English Video Translation System</div>
          <div className="mt-2 md:mt-0">Wise Design System · Sage Canvas `#e8ebe6` & Wise Green `#9fe870`</div>
        </div>
      </footer>
    </div>
  );
}
