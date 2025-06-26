import pytest
import sys
import os
from pathlib import Path


class TestSetupValidation:
    """Validation tests to ensure the testing infrastructure is properly configured."""
    
    def test_python_version(self):
        """Verify Python version is 3.8 or higher."""
        assert sys.version_info >= (3, 8), "Python 3.8 or higher is required"
    
    def test_pytest_installed(self):
        """Verify pytest is installed and importable."""
        import pytest
        assert pytest.__version__
    
    def test_pytest_cov_installed(self):
        """Verify pytest-cov is installed."""
        import pytest_cov
        assert pytest_cov.__version__
    
    def test_pytest_mock_installed(self):
        """Verify pytest-mock is installed."""
        import pytest_mock
        # pytest_mock doesn't expose __version__, just verify it can be imported
        assert pytest_mock
    
    def test_project_structure(self):
        """Verify the project structure is correct."""
        project_root = Path(__file__).parent.parent
        
        # Check essential directories exist
        assert project_root.exists()
        assert (project_root / "tests").exists()
        assert (project_root / "tests" / "unit").exists()
        assert (project_root / "tests" / "integration").exists()
        
        # Check configuration files exist
        assert (project_root / "pyproject.toml").exists()
        assert (project_root / ".gitignore").exists()
    
    def test_conftest_fixtures(self, temp_dir, mock_config, mock_plugin):
        """Verify conftest fixtures are working."""
        # Test temp_dir fixture
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Test mock_config fixture
        assert isinstance(mock_config, dict)
        assert "language" in mock_config
        assert mock_config["language"] == "ru"
        
        # Test mock_plugin fixture
        assert hasattr(mock_plugin, "name")
        assert mock_plugin.name == "test_plugin"
        assert mock_plugin.start(None) is True
    
    def test_audio_fixture(self, sample_audio_data):
        """Verify audio data fixture provides correct format."""
        assert "data" in sample_audio_data
        assert "sample_rate" in sample_audio_data
        assert sample_audio_data["sample_rate"] == 16000
        assert len(sample_audio_data["data"]) > 0
    
    def test_temp_plugin_dir(self, temp_plugin_dir):
        """Verify temporary plugin directory is created correctly."""
        assert temp_plugin_dir.exists()
        assert (temp_plugin_dir / "plugin_test.py").exists()
        
        # Verify the plugin can be imported
        sys.path.insert(0, str(temp_plugin_dir.parent))
        try:
            from plugins.plugin_test import Plugin
            plugin = Plugin()
            assert plugin.name == "test_plugin"
        finally:
            sys.path.pop(0)
    
    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit test marker works."""
        assert True
    
    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that integration test marker works."""
        assert True
    
    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that slow test marker works."""
        assert True
    
    def test_coverage_configuration(self):
        """Verify coverage is properly configured."""
        # This test will verify coverage is running when pytest is executed
        import coverage
        assert coverage.__version__
    
    def test_mock_fixtures(self, mock_voice_assistant_core, mock_tts_engine, mock_stt_engine):
        """Verify voice assistant mock fixtures work correctly."""
        # Test mock core
        assert mock_voice_assistant_core.language == "ru"
        assert mock_voice_assistant_core.is_running is True
        mock_voice_assistant_core.say("test")
        mock_voice_assistant_core.say.assert_called_with("test")
        
        # Test mock TTS
        assert mock_tts_engine.name == "mock_tts"
        assert mock_tts_engine.rate == 150
        
        # Test mock STT
        result = mock_stt_engine.recognize()
        assert result["text"] == "test command"
        assert result["confidence"] == 0.95
    
    def test_environment_reset(self):
        """Verify environment variables are set for testing."""
        assert os.environ.get("VA_TEST_MODE") == "1"
        assert os.environ.get("VA_LOG_LEVEL") == "DEBUG"
    
    def test_sample_command_context(self, sample_command_context):
        """Verify command context fixture provides proper structure."""
        assert "raw_text" in sample_command_context
        assert "intent" in sample_command_context
        assert sample_command_context["intent"] == "weather_forecast"
        assert sample_command_context["confidence"] == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])