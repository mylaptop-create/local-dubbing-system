import os
import json
import logging
from typing import Dict, Any, Callable, Optional, List
from pathlib import Path

from backend.database.manager import DatabaseManager
from backend.core.config import settings
from backend.providers.base import Segment
from backend.media.ffmpeg import MediaEngine
from backend.providers.transcription import SmartTranscriptionProvider
from backend.providers.translation import SmartTranslationProvider
from backend.providers.tts import SmartTTSProvider
from backend.media.alignment import AudioAligner
from backend.media.subtitles import SubtitleGenerator

logger = logging.getLogger(__name__)

STAGES = [
    "MEDIA_ANALYSIS",
    "AUDIO_EXTRACTION",
    "TRANSCRIPTION",
    "TRANSLATION",
    "SUBTITLE_GENERATION",
    "TTS",
    "AUDIO_ASSEMBLY",
    "VIDEO_RENDERING",
    "COMPLETE"
]

STAGE_PROGRESS_MAP = {
    "MEDIA_ANALYSIS": 5.0,
    "AUDIO_EXTRACTION": 15.0,
    "TRANSCRIPTION": 35.0,
    "TRANSLATION": 50.0,
    "SUBTITLE_GENERATION": 60.0,
    "TTS": 75.0,
    "AUDIO_ASSEMBLY": 88.0,
    "VIDEO_RENDERING": 98.0,
    "COMPLETE": 100.0
}

class PipelineOrchestrator:
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        media_engine: Optional[MediaEngine] = None,
        transcription_provider = None,
        translation_provider = None,
        tts_provider = None,
        progress_callback: Optional[Callable[[str, str, float, str], None]] = None
    ):
        self.db = db_manager or DatabaseManager()
        self.media_engine = media_engine or MediaEngine()
        self.transcription_provider = transcription_provider or SmartTranscriptionProvider()
        self.translation_provider = translation_provider or SmartTranslationProvider()
        self.tts_provider = tts_provider or SmartTTSProvider()
        self.aligner = AudioAligner(media_engine=self.media_engine)
        self.progress_callback = progress_callback

    def _notify_progress(self, project_id: str, stage: str, progress: float, msg: str):
        self.db.update_project_status(project_id, status="PROCESSING", current_stage=stage, progress_pct=progress)
        self.db.add_log(level="INFO", message=msg, project_id=project_id, stage=stage)
        if self.progress_callback:
            try:
                self.progress_callback(project_id, stage, progress, msg)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def run_pipeline(self, project_id: str, resume_from_stage: Optional[str] = None) -> Dict[str, Any]:
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project_dir = settings.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        checkpoints = {c["stage"]: c for c in self.db.get_checkpoints(project_id) if c["status"] == "COMPLETED"}

        # Initialize pipeline paths
        source_video = project["source_video_path"]
        extracted_audio = str(project_dir / "extracted_audio.wav")
        zh_srt_path = str(project_dir / "chinese_transcript.srt")
        en_srt_path = str(project_dir / "english_subtitles.srt")
        en_vtt_path = str(project_dir / "english_subtitles.vtt")
        assembled_audio = str(project_dir / "generated_english_audio.wav")
        final_video = str(project_dir / "final_english_video.mp4")

        cfg = project["config"]
        audio_mode = cfg.get("audio_mode", "replace")
        voice = cfg.get("tts_voice", "en-US-JennyNeural")
        burn_subtitles = cfg.get("burn_subtitles", False)

        segments = [Segment(**s) for s in project.get("segments", [])]
        media_info = {}

        try:
            # 1. MEDIA ANALYSIS
            if "MEDIA_ANALYSIS" not in checkpoints:
                self._notify_progress(project_id, "MEDIA_ANALYSIS", STAGE_PROGRESS_MAP["MEDIA_ANALYSIS"], "Analyzing source media file...")
                media_info = self.media_engine.probe(source_video)
                self.db.record_checkpoint(project_id, "MEDIA_ANALYSIS", "COMPLETED", {"media_info": media_info})
            else:
                media_info = checkpoints["MEDIA_ANALYSIS"]["output_files"].get("media_info", {})

            media_duration = media_info.get("duration", 10.0)

            # 2. AUDIO EXTRACTION
            if "AUDIO_EXTRACTION" not in checkpoints:
                self._notify_progress(project_id, "AUDIO_EXTRACTION", STAGE_PROGRESS_MAP["AUDIO_EXTRACTION"], "Extracting audio from video...")
                self.media_engine.extract_audio(source_video, extracted_audio)
                self.db.record_checkpoint(project_id, "AUDIO_EXTRACTION", "COMPLETED", {"audio_path": extracted_audio})

            # 3. TRANSCRIPTION
            if "TRANSCRIPTION" not in checkpoints or not segments:
                self._notify_progress(project_id, "TRANSCRIPTION", STAGE_PROGRESS_MAP["TRANSCRIPTION"], "Transcribing Chinese audio...")
                trans_res = self.transcription_provider.transcribe(extracted_audio, language=project["source_lang"])
                segments = trans_res.segments
                self.db.update_project_status(project_id, "PROCESSING", "TRANSCRIPTION", STAGE_PROGRESS_MAP["TRANSCRIPTION"], [s.model_dump() for s in segments])
                self.db.record_checkpoint(project_id, "TRANSCRIPTION", "COMPLETED", {"segments_count": len(segments)})

            # 4. TRANSLATION
            if "TRANSLATION" not in checkpoints or not any(s.translated_text for s in segments):
                self._notify_progress(project_id, "TRANSLATION", STAGE_PROGRESS_MAP["TRANSLATION"], "Translating Chinese segments to English...")
                segments = self.translation_provider.translate_segments(segments, source_lang=project["source_lang"], target_lang=project["target_lang"])
                self.db.update_project_status(project_id, "PROCESSING", "TRANSLATION", STAGE_PROGRESS_MAP["TRANSLATION"], [s.model_dump() for s in segments])
                self.db.record_checkpoint(project_id, "TRANSLATION", "COMPLETED", {"translated": True})

            # 5. SUBTITLE GENERATION
            if "SUBTITLE_GENERATION" not in checkpoints:
                self._notify_progress(project_id, "SUBTITLE_GENERATION", STAGE_PROGRESS_MAP["SUBTITLE_GENERATION"], "Generating English and Chinese subtitle files...")
                SubtitleGenerator.generate_srt(segments, zh_srt_path, use_translation=False)
                SubtitleGenerator.generate_srt(segments, en_srt_path, use_translation=True)
                SubtitleGenerator.generate_vtt(segments, en_vtt_path, use_translation=True)
                self.db.record_checkpoint(project_id, "SUBTITLE_GENERATION", "COMPLETED", {
                    "chinese_srt": zh_srt_path,
                    "english_srt": en_srt_path,
                    "english_vtt": en_vtt_path
                })

            # 6. TTS GENERATION & ALIGNMENT
            if "TTS" not in checkpoints or not all(s.audio_path and os.path.exists(s.audio_path) for s in segments):
                self._notify_progress(project_id, "TTS", STAGE_PROGRESS_MAP["TTS"], "Generating and timing-aligning English speech clips...")
                tts_dir = project_dir / "tts_segments"
                tts_dir.mkdir(exist_ok=True)

                for idx, seg in enumerate(segments):
                    if not seg.translated_text:
                        continue
                    raw_tts_file = str(tts_dir / f"raw_seg_{seg.id}.wav")
                    aligned_tts_file = str(tts_dir / f"aligned_seg_{seg.id}.wav")

                    self.tts_provider.generate_speech(seg.translated_text, raw_tts_file, voice=voice)
                    self.aligner.align_segment_audio(seg, raw_tts_file, aligned_tts_file)
                    seg.audio_path = aligned_tts_file

                self.db.update_project_status(project_id, "PROCESSING", "TTS", STAGE_PROGRESS_MAP["TTS"], [s.model_dump() for s in segments])
                self.db.record_checkpoint(project_id, "TTS", "COMPLETED", {"tts_count": len(segments)})

            # 7. AUDIO ASSEMBLY
            if "AUDIO_ASSEMBLY" not in checkpoints:
                self._notify_progress(project_id, "AUDIO_ASSEMBLY", STAGE_PROGRESS_MAP["AUDIO_ASSEMBLY"], "Assembling timeline-aligned audio...")
                raw_full_audio = str(project_dir / "raw_assembled_speech.wav")
                self.aligner.assemble_full_audio(segments, total_media_duration=media_duration, output_audio_path=raw_full_audio)

                # Mix with original video if ducking requested
                self.media_engine.mix_audio(
                    original_video_path=source_video,
                    dubbed_audio_path=raw_full_audio,
                    output_audio_path=assembled_audio,
                    mode=audio_mode
                )
                self.db.record_checkpoint(project_id, "AUDIO_ASSEMBLY", "COMPLETED", {"assembled_audio": assembled_audio})

            # 8. VIDEO RENDERING
            if "VIDEO_RENDERING" not in checkpoints:
                self._notify_progress(project_id, "VIDEO_RENDERING", STAGE_PROGRESS_MAP["VIDEO_RENDERING"], "Rendering final dubbed video...")
                self.media_engine.render_final_video(
                    video_path=source_video,
                    audio_path=assembled_audio,
                    output_video_path=final_video,
                    subtitle_path=en_srt_path,
                    burn_subtitles=burn_subtitles
                )
                self.db.record_checkpoint(project_id, "VIDEO_RENDERING", "COMPLETED", {"final_video": final_video})

            # 9. COMPLETE
            self._notify_progress(project_id, "COMPLETE", STAGE_PROGRESS_MAP["COMPLETE"], "Project translation and dubbing successfully completed.")
            self.db.update_project_status(project_id, status="COMPLETED", current_stage="COMPLETE", progress_pct=100.0)

            return self.db.get_project(project_id)

        except Exception as e:
            logger.error(f"Pipeline error on project {project_id}: {e}", exc_info=True)
            self.db.update_project_status(project_id, status="FAILED", current_stage=project.get("current_stage", "UNKNOWN"), progress_pct=project.get("progress_pct", 0.0))
            self.db.record_checkpoint(project_id, project.get("current_stage", "UNKNOWN"), "FAILED", {}, error_message=str(e))
            self.db.add_log(level="ERROR", message=f"Pipeline failed: {e}", project_id=project_id)
            raise e
