# Archive Notes - Claude Code Tracer

## Project Status: ARCHIVED (2025-07-13)

### Why This Project Was Archived

This project aimed to transparently monitor and record Claude CLI sessions using PTY (pseudo-terminal) monitoring. However, we encountered insurmountable technical challenges:

1. **Complex UI Rendering**: Claude CLI uses a sophisticated terminal UI with:
   - Constant screen updates and redraws
   - Animated status indicators (Honking…, Processing…, Wrangling…, Coalescing…)
   - Rich text formatting with extensive ANSI escape sequences
   - Dynamic UI elements that update in real-time

2. **Technical Limitations**:
   - PTY captures raw terminal output including all control sequences
   - Cleaning the output while preserving conversation content proved extremely difficult
   - Animation frames generate massive amounts of noise data
   - No clean separation between UI elements and actual conversation content

### What We Tried

1. **PTY Monitoring (Primary Approach)**
   - Successfully captured raw terminal I/O
   - Implemented ANSI escape sequence stripping
   - Added animation detection and filtering
   - Result: Partial success but unreliable content extraction

2. **pexpect Library**
   - Issues with byte/string handling
   - Difficulty synchronizing with Claude's interactive UI
   - Result: More problems than PTY approach

3. **script Command**
   - Standard Unix tool for terminal recording
   - Same issues as PTY (captures all terminal output)
   - Result: No improvement over direct PTY

4. **tmux pipe-pane**
   - Attempted to use tmux's output streaming
   - Result: Same fundamental issues with UI noise

### Lessons Learned

1. **UI Complexity**: Modern CLIs with rich, animated UIs are difficult to monitor transparently
2. **Need for Official Support**: Clean session logging requires cooperation from the CLI application
3. **Alternative Approaches**: 
   - Direct API usage would be cleaner but defeats the purpose of CLI monitoring
   - Waiting for official logging features is the most practical approach

### Future Possibilities

1. **Official Logging**: If Anthropic adds session logging to Claude CLI
2. **Export Features**: Built-in session export functionality
3. **Simpler UI Mode**: A "simple" or "plain" output mode for Claude CLI
4. **API Integration**: Direct integration with Claude API instead of CLI monitoring

### Code State

The codebase demonstrates:
- Working PTY monitoring implementation
- Comprehensive ANSI escape sequence handling
- Session storage architecture (local + Supabase)
- Privacy protection framework

While not production-ready for Claude CLI, the code could be adapted for monitoring simpler CLI applications.

### Contact

If you're interested in this problem space or have ideas for solutions, feel free to fork and experiment. The fundamental PTY monitoring approach is sound; the challenge is specific to Claude CLI's UI complexity.

---

*Archived by: Yusuke Sato*  
*Date: 2025-07-13*  
*Reason: Technical limitations with Claude CLI's animated UI*