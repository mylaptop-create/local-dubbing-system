export interface ProjectConfig {
  tts_voice: string;
  audio_mode: 'replace' | 'duck';
  burn_subtitles: boolean;
  original_filename?: string;
}

export interface Segment {
  id: number;
  start: number;
  end: number;
  text: string;
  translated_text?: string;
  audio_path?: string;
}

export interface Checkpoint {
  id: number;
  project_id: string;
  stage: string;
  status: string;
  output_files: Record<string, any>;
  error_message?: string;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  source_video_path: string;
  source_lang: string;
  target_lang: string;
  status: 'CREATED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  current_stage: string;
  progress_pct: number;
  config: ProjectConfig;
  segments: Segment[];
  checkpoints?: Checkpoint[];
  created_at: string;
  updated_at: string;
}

export interface SystemDiagnostics {
  os: string;
  os_release: string;
  platform: string;
  python_version: string;
  cpu_count: number;
  ram_total_gb: number;
  ram_available_gb: number;
  ram_percent: number;
  disk_total_gb: number;
  disk_free_gb: number;
  gpu: {
    available: boolean;
    name?: string;
    vram_mb: number;
    vram_gb: number;
    type: string;
    cuda_available: boolean;
  };
  ffmpeg: {
    available: boolean;
    path?: string;
    type: string;
  };
}

export interface Voice {
  id: string;
  name: string;
  gender: string;
  language: string;
  provider: string;
}

export interface StorageInfo {
  models_size_mb: number;
  projects_size_mb: number;
  temp_size_mb: number;
  disk_free_gb: number;
  disk_total_gb: number;
}

export interface LogEntry {
  id: number;
  project_id?: string;
  level: string;
  stage?: string;
  message: string;
  created_at: string;
}
