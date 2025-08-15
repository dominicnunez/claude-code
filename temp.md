// /hooks/multi_agent/config/language_agents.json
{
  "languages": {
    "go": {
      "architect": "gad",
      "developer": "god",
      "confidence_threshold": 0.8,
      "file_extensions": [".go"],
      "config_files": ["go.mod", "go.sum"]
    },
    "python": {
      "architect": "pyad",
      "developer": "pydv",
      "confidence_threshold": 0.8,
      "file_extensions": [".py"],
      "config_files": ["pyproject.toml", "requirements.txt"]
    }
  }
}
