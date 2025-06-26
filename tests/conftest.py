import pytest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
from datetime import datetime


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config():
    """Provide a mock configuration dictionary."""
    return {
        "language": "ru",
        "plugins": ["plugin_example", "plugin_test"],
        "tts_engine": "vosk",
        "stt_engine": "vosk",
        "model_path": "/tmp/test_model",
        "options": {
            "debug": True,
            "log_level": "INFO",
            "audio_device": "default",
        }
    }


@pytest.fixture
def mock_plugin():
    """Create a mock plugin object."""
    plugin = Mock()
    plugin.name = "test_plugin"
    plugin.version = "1.0.0"
    plugin.start = Mock(return_value=True)
    plugin.stop = Mock(return_value=True)
    plugin.process = Mock(return_value={"status": "success"})
    return plugin


@pytest.fixture
def sample_audio_data():
    """Provide sample audio data for testing."""
    import numpy as np
    sample_rate = 16000
    duration = 1.0  # 1 second
    samples = int(sample_rate * duration)
    # Generate a simple sine wave
    frequency = 440  # A4 note
    t = np.linspace(0, duration, samples, False)
    audio = np.sin(2 * np.pi * frequency * t) * 0.5
    return {
        "data": audio.astype(np.float32),
        "sample_rate": sample_rate,
        "duration": duration,
        "channels": 1
    }


@pytest.fixture
def mock_voice_assistant_core():
    """Create a mock VoiceAssistantCore object."""
    core = MagicMock()
    core.language = "ru"
    core.plugins = {}
    core.tts_engine = Mock()
    core.stt_engine = Mock()
    core.is_running = True
    core.say = Mock()
    core.listen = Mock(return_value="test command")
    core.process_command = Mock(return_value=True)
    return core


@pytest.fixture
def temp_plugin_dir(temp_dir):
    """Create a temporary plugin directory with sample plugin."""
    plugin_dir = temp_dir / "plugins"
    plugin_dir.mkdir()
    
    # Create a sample plugin file
    plugin_file = plugin_dir / "plugin_test.py"
    plugin_content = '''
class Plugin:
    def __init__(self):
        self.name = "test_plugin"
        self.version = "1.0.0"
        self.description = "Test plugin for unit tests"
    
    def start(self, core):
        self.core = core
        return True
    
    def stop(self):
        return True
    
    def process(self, command):
        return {"status": "processed", "command": command}
'''
    plugin_file.write_text(plugin_content)
    
    return plugin_dir


@pytest.fixture
def sample_options_file(temp_dir):
    """Create a sample options.json file."""
    options_file = temp_dir / "options.json"
    options_data = {
        "language": "ru",
        "tts": {
            "engine": "vosk",
            "voice": "default",
            "rate": 150,
            "volume": 0.9
        },
        "stt": {
            "engine": "vosk",
            "model_path": "/path/to/model",
            "sample_rate": 16000
        },
        "plugins": {
            "enabled": ["plugin_example", "plugin_weather"],
            "disabled": ["plugin_test"]
        }
    }
    options_file.write_text(json.dumps(options_data, indent=2))
    return options_file


@pytest.fixture
def mock_web_request():
    """Create a mock for web requests."""
    response = Mock()
    response.status_code = 200
    response.json = Mock(return_value={"status": "ok", "data": "test"})
    response.text = '{"status": "ok", "data": "test"}'
    response.content = b'{"status": "ok", "data": "test"}'
    return response


@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime for consistent testing."""
    fixed_datetime = datetime(2024, 1, 15, 12, 30, 45)
    
    class MockDatetime:
        @classmethod
        def now(cls):
            return fixed_datetime
        
        @classmethod
        def utcnow(cls):
            return fixed_datetime
    
    monkeypatch.setattr('datetime.datetime', MockDatetime)
    return fixed_datetime


@pytest.fixture
def sample_command_context():
    """Provide a sample command context for testing."""
    return {
        "raw_text": "какая погода завтра",
        "normalized_text": "какая погода завтра",
        "intent": "weather_forecast",
        "entities": {
            "time": "tomorrow",
            "location": None
        },
        "confidence": 0.95,
        "timestamp": datetime.now().isoformat(),
        "source": "microphone",
        "user_id": "test_user"
    }


@pytest.fixture
def mock_audio_device():
    """Mock audio device for testing."""
    device = Mock()
    device.name = "Test Audio Device"
    device.channels = 2
    device.sample_rate = 48000
    device.is_input = True
    device.is_output = True
    device.latency = 0.01
    return device


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables for each test."""
    # Store original environment
    original_env = os.environ.copy()
    
    # Set test environment variables
    monkeypatch.setenv("VA_TEST_MODE", "1")
    monkeypatch.setenv("VA_LOG_LEVEL", "DEBUG")
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def capture_logs():
    """Capture log messages during tests."""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    yield log_capture
    
    # Remove handler after test
    root_logger.removeHandler(handler)


@pytest.fixture
def mock_tts_engine():
    """Mock TTS engine for testing."""
    engine = Mock()
    engine.name = "mock_tts"
    engine.voices = ["voice1", "voice2"]
    engine.current_voice = "voice1"
    engine.rate = 150
    engine.volume = 0.9
    engine.say = Mock()
    engine.save_to_file = Mock()
    engine.is_speaking = Mock(return_value=False)
    return engine


@pytest.fixture
def mock_stt_engine():
    """Mock STT engine for testing."""
    engine = Mock()
    engine.name = "mock_stt"
    engine.model_path = "/tmp/model"
    engine.sample_rate = 16000
    engine.recognize = Mock(return_value={"text": "test command", "confidence": 0.95})
    engine.is_listening = Mock(return_value=False)
    return engine