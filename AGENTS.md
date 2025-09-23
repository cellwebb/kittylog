# Agents in kittylog

The kittylog project uses AI agents to analyze git commit history and generate changelog entries in the "Keep a Changelog" format.

## Key Agents

1. **Changelog Generation Agent** - Analyzes commit messages and generates structured changelog content
2. **Tag Analysis Agent** - Identifies git tags and determines version ranges for changelog entries
3. **Content Formatting Agent** - Ensures generated entries adhere to Keep a Changelog standards
4. **Postprocessing Agent** - Cleans up and formats content to prevent information overload

## Agent Integration Points

- **ai.py** module interfaces with various LLM providers (OpenAI, Anthropic, etc.)
- **prompt.py** shapes commit data into structured prompts for agent consumption
- **changelog.py** incorporates agent-generated content into changelog files
- **postprocess.py** refines agent output for better readability and compliance

These agents work together to automate changelog creation while maintaining quality and standards adherence.