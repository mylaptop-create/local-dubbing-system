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
  Cpu
} from 'lucide-react';
import type { Project, SystemDiagnostics, Voice, StorageInfo, LogEntry } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'new' | 'projects' | 'queue' | 'diagnostics' | 'storage' | 'logs'>('new');
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [storage, setStorage] = useState<StorageInfo | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Form State
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [projectName, setProjectName] = useState('');
  const [ttsVoice, setTtsVoice] = useState('en-US-JennyNeural');
  const [audioMode, setAudioMode] = useState<'replace' | 'duck'>('replace');
  const [burnSubtitles, setBurnSubtitles] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Live socket & fetch polling
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
    if (!videoFile || !projectName) return;
    setIsSubmitting(true);

    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('name', projectName);
    formData.append('source_lang', 'zh');
    formData.append('target_lang', 'en');
    formData.append('tts_voice', ttsVoice);
    formData.append('audio_mode', audioMode);
    formData.append('burn_subtitles', String(burnSubtitles));

    try {
      const res = await fetch('/api/projects', {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const createdProject = await res.json();
        await fetch(`/api/projects/${createdProject.id}/start`, { method: 'POST' });
        setVideoFile(null);
        setProjectName('');
        await fetchProjects();
        setSelectedProject(createdProject);
        setActiveTab('queue');
      }
    } catch (e) {
      alert('Failed to create project.');
    } finally {
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
    <div className="flex h-screen bg-slate-900 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between p-4">
        <div>
          <div className="flex items-center space-x-3 mb-8 px-2">
            <Video className="w-7 h-7 text-indigo-400" />
            <div>
              <h1 className="font-bold text-lg leading-none text-white">VideoDub AI</h1>
              <p className="text-xs text-slate-400 mt-1">ZH → EN Local Studio</p>
            </div>
          </div>

          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('new')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'new' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <PlusCircle className="w-5 h-5" />
              <span>New Translation</span>
            </button>

            <button
              onClick={() => setActiveTab('projects')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'projects' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <List className="w-5 h-5" />
              <span>My Projects ({projects.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('queue')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'queue' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Activity className="w-5 h-5" />
              <span>Processing Queue</span>
            </button>

            <button
              onClick={() => setActiveTab('diagnostics')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'diagnostics' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-5 h-5" />
              <span>System Health</span>
            </button>

            <button
              onClick={() => setActiveTab('storage')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'storage' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <HardDrive className="w-5 h-5" />
              <span>Storage</span>
            </button>

            <button
              onClick={() => setActiveTab('logs')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'logs' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <FileText className="w-5 h-5" />
              <span>System Logs</span>
            </button>
          </nav>
        </div>

        {diagnostics && (
          <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl text-xs space-y-1">
            <div className="text-slate-400 font-semibold flex justify-between items-center">
              <span>Hardware</span>
              <span className="text-emerald-400">Local</span>
            </div>
            <div className="text-slate-300">GPU: {diagnostics.gpu.available ? diagnostics.gpu.name : 'CPU Fallback'}</div>
            <div className="text-slate-400">RAM: {diagnostics.ram_available_gb}GB Free</div>
          </div>
        )}
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-8">
        {/* NEW TRANSLATION TAB */}
        {activeTab === 'new' && (
          <div className="max-w-3xl mx-auto">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white">Create New Video Dubbing Project</h2>
              <p className="text-slate-400 text-sm mt-1">
                Upload Chinese video to automatically transcribe, translate, synthesize English voice, and generate dubbed video.
              </p>
            </div>

            <form onSubmit={handleCreateProject} className="bg-slate-950 border border-slate-800 p-6 rounded-2xl space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Video File</label>
                <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-900/50">
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
                    <Video className="w-10 h-10 mx-auto text-indigo-400 mb-2" />
                    {videoFile ? (
                      <p className="text-emerald-400 font-medium">{videoFile.name} ({(videoFile.size / (1024 * 1024)).toFixed(1)} MB)</p>
                    ) : (
                      <p className="text-slate-400 text-sm">Drag and drop Chinese video here or click to browse</p>
                    )}
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Project Name</label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Course 01 - Intro"
                  required
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Target Voice</label>
                  <select
                    value={ttsVoice}
                    onChange={(e) => setTtsVoice(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    {voices.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name} ({v.gender})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Audio Mode</label>
                  <select
                    value={audioMode}
                    onChange={(e) => setAudioMode(e.target.value as any)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="replace">Replace original audio</option>
                    <option value="duck">Ducking (Keep original low background volume)</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="burn-sub"
                  checked={burnSubtitles}
                  onChange={(e) => setBurnSubtitles(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-900 border-slate-700"
                />
                <label htmlFor="burn-sub" className="text-sm text-slate-300">
                  Burn English subtitles permanently into video (otherwise embedded soft subtitles)
                </label>
              </div>

              <button
                type="submit"
                disabled={!videoFile || isSubmitting}
                className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl shadow-lg transition-all flex items-center justify-center space-x-2 cursor-pointer"
              >
                <Play className="w-5 h-5 fill-current" />
                <span>{isSubmitting ? 'Creating Project...' : 'Start Translation & Dubbing'}</span>
              </button>
            </form>
          </div>
        )}

        {/* MY PROJECTS TAB */}
        {activeTab === 'projects' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">My Projects</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {projects.map((p) => (
                <div key={p.id} className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-lg text-white">{p.name}</h3>
                      <p className="text-xs text-slate-400">ID: {p.id}</p>
                    </div>
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                        p.status === 'COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : p.status === 'FAILED'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      {p.status}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Stage: {p.current_stage}</span>
                      <span>{p.progress_pct.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                      <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${p.progress_pct}%` }} />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <button
                      onClick={() => {
                        setSelectedProject(p);
                        setActiveTab('queue');
                      }}
                      className="text-indigo-400 hover:text-indigo-300 text-xs font-medium cursor-pointer"
                    >
                      View Details & Outputs →
                    </button>
                    <div className="flex space-x-2">
                      {p.status === 'FAILED' && (
                        <button
                          onClick={() => handleResume(p.id)}
                          className="p-1.5 text-slate-400 hover:text-amber-400 hover:bg-slate-800 rounded cursor-pointer"
                          title="Resume"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded cursor-pointer"
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
            <h2 className="text-2xl font-bold text-white">Pipeline Execution Status</h2>

            {selectedProject ? (
              <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 space-y-6">
                <div className="flex justify-between items-center border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white">{selectedProject.name}</h3>
                    <p className="text-xs text-slate-400">Project ID: {selectedProject.id}</p>
                  </div>
                  <div className="flex items-center space-x-3">
                    {selectedProject.status === 'FAILED' && (
                      <button
                        onClick={() => handleResume(selectedProject.id)}
                        className="bg-amber-600 hover:bg-amber-500 px-4 py-1.5 rounded-lg text-sm font-medium text-white flex items-center space-x-2 cursor-pointer"
                      >
                        <RotateCcw className="w-4 h-4" />
                        <span>Resume Pipeline</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm font-medium text-slate-300">
                    <span>Current Stage: {selectedProject.current_stage}</span>
                    <span>{selectedProject.progress_pct.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full transition-all duration-500"
                      style={{ width: `${selectedProject.progress_pct}%` }}
                    />
                  </div>
                </div>

                {/* Outputs section if completed */}
                {selectedProject.status === 'COMPLETED' && (
                  <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl space-y-3">
                    <h4 className="font-semibold text-emerald-400 text-sm flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Generated Artifacts & Downloads</span>
                    </h4>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <a
                        href={`/api/projects/${selectedProject.id}/files/final_english_video.mp4`}
                        download
                        className="bg-slate-800 hover:bg-slate-700 p-3 rounded-lg border border-slate-700 flex items-center justify-between text-slate-200"
                      >
                        <span>final_english_video.mp4</span>
                        <Download className="w-4 h-4 text-indigo-400" />
                      </a>
                      <a
                        href={`/api/projects/${selectedProject.id}/files/english_subtitles.srt`}
                        download
                        className="bg-slate-800 hover:bg-slate-700 p-3 rounded-lg border border-slate-700 flex items-center justify-between text-slate-200"
                      >
                        <span>english_subtitles.srt</span>
                        <Download className="w-4 h-4 text-indigo-400" />
                      </a>
                      <a
                        href={`/api/projects/${selectedProject.id}/files/chinese_transcript.srt`}
                        download
                        className="bg-slate-800 hover:bg-slate-700 p-3 rounded-lg border border-slate-700 flex items-center justify-between text-slate-200"
                      >
                        <span>chinese_transcript.srt</span>
                        <Download className="w-4 h-4 text-indigo-400" />
                      </a>
                      <a
                        href={`/api/projects/${selectedProject.id}/files/generated_english_audio.wav`}
                        download
                        className="bg-slate-800 hover:bg-slate-700 p-3 rounded-lg border border-slate-700 flex items-center justify-between text-slate-200"
                      >
                        <span>generated_english_audio.wav</span>
                        <Download className="w-4 h-4 text-indigo-400" />
                      </a>
                    </div>
                  </div>
                )}

                {/* Segments Preview */}
                {selectedProject.segments && selectedProject.segments.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-semibold text-slate-200 text-sm">Transcript & Translation Segments</h4>
                    <div className="max-h-60 overflow-y-auto space-y-2 border border-slate-800 p-3 rounded-xl bg-slate-900/40">
                      {selectedProject.segments.map((seg) => (
                        <div key={seg.id} className="text-xs p-2.5 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-indigo-400 font-mono">
                            [{seg.start.toFixed(2)}s → {seg.end.toFixed(2)}s]
                          </div>
                          <div className="text-slate-300">ZH: {seg.text}</div>
                          {seg.translated_text && <div className="text-emerald-400">EN: {seg.translated_text}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-slate-400">Select a project from "My Projects" to inspect progress and artifacts.</p>
            )}
          </div>
        )}

        {/* SYSTEM DIAGNOSTICS TAB */}
        {activeTab === 'diagnostics' && diagnostics && (
          <div className="max-w-3xl mx-auto space-y-6">
            <h2 className="text-2xl font-bold text-white">System Diagnostics</h2>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-2">
                <h3 className="text-slate-400 text-xs font-semibold uppercase">Operating System</h3>
                <p className="text-xl font-bold text-white">{diagnostics.os}</p>
                <p className="text-xs text-slate-400">{diagnostics.platform}</p>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-2">
                <h3 className="text-slate-400 text-xs font-semibold uppercase">GPU Acceleration</h3>
                <p className="text-xl font-bold text-emerald-400">
                  {diagnostics.gpu.available ? diagnostics.gpu.name : 'CPU Fallback Active'}
                </p>
                <p className="text-xs text-slate-400">
                  {diagnostics.gpu.available ? `VRAM: ${diagnostics.gpu.vram_gb} GB` : 'No CUDA GPU detected; executing on CPU'}
                </p>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-2">
                <h3 className="text-slate-400 text-xs font-semibold uppercase">Memory (RAM)</h3>
                <p className="text-xl font-bold text-white">{diagnostics.ram_available_gb} GB Free</p>
                <p className="text-xs text-slate-400">Total System RAM: {diagnostics.ram_total_gb} GB</p>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-2">
                <h3 className="text-slate-400 text-xs font-semibold uppercase">FFmpeg Engine</h3>
                <p className="text-xl font-bold text-white">{diagnostics.ffmpeg.available ? 'Ready' : 'Not Found'}</p>
                <p className="text-xs text-slate-400 truncate">{diagnostics.ffmpeg.path || 'N/A'}</p>
              </div>
            </div>
          </div>
        )}

        {/* STORAGE TAB */}
        {activeTab === 'storage' && storage && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-white">Storage Management</h2>
              <button
                onClick={handleCleanTemp}
                className="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg text-sm text-slate-200 border border-slate-700 cursor-pointer"
              >
                Clean Temporary Files
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-1">
                <div className="text-slate-400 text-xs font-medium">Projects Storage</div>
                <div className="text-2xl font-bold text-white">{storage.projects_size_mb} MB</div>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-1">
                <div className="text-slate-400 text-xs font-medium">Model Cache</div>
                <div className="text-2xl font-bold text-white">{storage.models_size_mb} MB</div>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-1">
                <div className="text-slate-400 text-xs font-medium">Free Disk Space</div>
                <div className="text-2xl font-bold text-emerald-400">{storage.disk_free_gb} GB</div>
              </div>
            </div>
          </div>
        )}

        {/* SYSTEM LOGS TAB */}
        {activeTab === 'logs' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white">System Logs</h2>
            <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl font-mono text-xs max-h-96 overflow-y-auto space-y-2">
              {logs.map((l) => (
                <div key={l.id} className="text-slate-300 border-b border-slate-900 pb-1">
                  <span className="text-slate-500">[{l.created_at}]</span>{' '}
                  <span className={l.level === 'ERROR' ? 'text-rose-400' : 'text-indigo-400'}>[{l.level}]</span>{' '}
                  {l.stage && <span className="text-amber-400">[{l.stage}]</span>} {l.message}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
