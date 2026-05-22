```
{
	"servers": {
		"io.github.github/github-mcp-server-remote": {
			"type": "http",
			"url": "https://api.githubcopilot.com/mcp/",
			"gallery": "https://api.mcp.github.com",
			"version": "0.31.0"
		},
		
		"github-mcp-server-localDocker": {
            "type": "stdio",
            "command": "docker",
            "args": [
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_TOKEN",
            "-e",
            "GITHUB_REPO",
            "ghcr.io/github/github-mcp-server:latest"
            ],
            "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:GITHUB_TOKEN}",
            "GITHUB_REPO": "${input:GITHUB_REPO}"
            },
            "gallery": "https://api.mcp.github.com"
            }                   
	},
	"inputs": [
		{
		"id": "GITHUB_TOKEN",
		"type": "promptString",
		"description": "GitHub PAT with repo and workflow scopes",
		"password": true
		},
		{
		"id": "GITHUB_REPO",
		"type": "promptString",
		"description": "Repository in owner/repo format",
		"password": false
		}
	]
}
```

