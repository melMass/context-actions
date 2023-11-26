**EXPERIMENTAL DO NOT USE**

# win-context-menus


POC to understand windows shell extension for context menus, I since discovered this [blogpost](https://mrlixm.github.io/blog/windows-explorer-context-menu/) and the author published a much better lib for the same goals: [MrLixm/reg-file-creator](https://github.com/MrLixm/Reg-file-creator)

*note: I use context-menu-manager (on Scoop) to remove existing context menus*

### Structure

- `actions`: contain scripts used directly by the context menus that will get installed to `C:/context-actions`
- `bin`: binaries/script to generate files from JSON definitions
- `bucket`: context menu definition in JSON format (used by the generator)
