import logging
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

from agent.prompts import *
from agent.states import *
from agent.tools import write_file, read_file, get_current_directory, list_files

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize different LLMs for different tasks
# Use gpt-4o for strategic planning, gpt-4o-mini for coding (cost optimization)
planner_llm = ChatOpenAI(
    model="gpt-4o",  # More creative and comprehensive planning
    temperature=0.8,
)

architect_llm = ChatOpenAI(
    model="gpt-4o",  # Better at breaking down complex structures
    temperature=0.7,
)

coder_llm = ChatOpenAI(
    model="gpt-4o-mini",  # Fast and efficient for code generation
    temperature=0.6,
)

reviewer_llm = ChatOpenAI(
    model="gpt-4o",  # Critical eye for quality review
    temperature=0.5,
)


# Agent Functions
def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan with design excellence"""
    logger.info("=== PLANNER AGENT STARTED ===")
    user_prompt = state["user_prompt"]
    logger.info(f"User prompt: {user_prompt}")
    
    # Detect styling framework preference
    framework = "custom modern css"
    if "tailwind" in user_prompt.lower():
        framework = "TailwindCSS via CDN"
    elif "bootstrap" in user_prompt.lower():
        framework = "Bootstrap 5 via CDN"
    
    # Enhanced prompt with design guidelines
    enhanced_prompt = f"""
{planner_prompt(user_prompt)}

DESIGN EXCELLENCE REQUIREMENTS (Lovable.dev Quality Standards):

1. VISUAL DESIGN - STUNNING & PROFESSIONAL:
   - Beautiful, modern aesthetic that makes users say "WOW!"
   - Rich, vibrant color schemes with gradients and depth
   - Professional background colors (NOT plain white - use subtle gradients, patterns, or colors)
   - Proper visual hierarchy with clear focal points
   - Generous white space and breathing room
   - Contemporary UI patterns: glassmorphism, neumorphism, subtle shadows
   - Smooth animations and transitions on hover/interaction
   - Premium feel with attention to micro-details

2. LAYOUT & RESPONSIVENESS:
   - Mobile-first responsive design
   - Use CSS Grid for page layouts
   - Use Flexbox for component layouts
   - Breakpoints: mobile (< 640px), tablet (640-1024px), desktop (> 1024px)
   - Smooth transitions between breakpoints

3. TYPOGRAPHY:
   - Readable font sizes (16px base minimum)
   - Proper line heights (1.5-1.7 for body text)
   - Font hierarchy (h1: 2.5rem, h2: 2rem, h3: 1.5rem, etc.)
   - Consider Google Fonts for modern typography
   - Good contrast ratios (WCAG AA compliant)

4. COLORS & THEMING - BEAUTIFUL PALETTES:
   - Use CSS custom properties (variables) for easy theming
   - Rich color palette: primary, secondary, accent, neutral, success, error
   - Background colors: Use gradients, subtle patterns, or rich colors (NO plain white!)
   - Example beautiful backgrounds:
     * Linear gradients: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
     * Radial gradients: radial-gradient(circle at top right, #f093fb 0%, #f5576c 100%)
     * Subtle patterns with background-image
   - Dark mode support with CSS variables
   - Proper contrast ratios for accessibility
   - Color psychology: warm colors for energy, cool colors for calm

5. INTERACTIONS & ANIMATIONS - DELIGHTFUL UX:
   - Smooth transitions (0.3s ease default)
   - Engaging hover effects: scale, shadow, color shifts
   - Loading states with spinners or skeleton screens
   - Micro-interactions that delight users
   - Button press animations (scale down slightly on click)
   - Form focus states with glowing borders
   - Scroll animations for elements entering viewport
   - Smooth page transitions
   - Cursor changes to indicate interactivity

6. MODERN CSS FEATURES:
   - CSS Grid and Flexbox
   - CSS custom properties (variables)
   - Modern shadows: box-shadow with subtle depth
   - Backdrop filters for glassmorphism
   - Gradient backgrounds
   - Border radius for softness

7. ACCESSIBILITY:
   - Semantic HTML5 elements
   - ARIA labels where needed
   - Keyboard navigation support
   - Focus states clearly visible
   - Alt text for images
   - Proper heading hierarchy

STYLING FRAMEWORK: {framework}
{f"- Include proper CDN link in HTML" if "CDN" in framework else "- Implement custom modern CSS with variables"}

TECHNICAL BEST PRACTICES:
- Clean, semantic HTML5 structure
- Modular, organized CSS (consider BEM methodology)
- Modern JavaScript (ES6+)
- Progressive enhancement
- Performance optimization
- Cross-browser compatibility

Remember: The goal is to create websites that make users say "Wow, this looks professional!"
"""
    
    resp = planner_llm.with_structured_output(Plan).invoke(enhanced_prompt)
    if resp is None:
        logger.error("Planner did not return a valid response.")
        raise ValueError("Planner did not return a valid response.")
    
    logger.info(f"Plan created with design guidelines: {resp}")
    logger.info("=== PLANNER AGENT COMPLETED ===")
    return {"plan": resp}


def architect_agent(state: dict) -> dict:
    """Creates detailed TaskPlan from Plan"""
    logger.info("=== ARCHITECT AGENT STARTED ===")
    plan: Plan = state["plan"]
    logger.info(f"Processing plan: {plan.model_dump_json()}")
    
    resp = architect_llm.with_structured_output(TaskPlan).invoke(
        architect_prompt(plan=plan.model_dump_json())
    )
    if resp is None:
        logger.error("Architect did not return a valid response.")
        raise ValueError("Architect did not return a valid response.")

    resp.plan = plan
    logger.info(f"Task plan created with {len(resp.implementation_steps)} steps")
    logger.info("=== ARCHITECT AGENT COMPLETED ===")
    return {"task_plan": resp}


def coder_agent(state: dict) -> dict:
    """LangGraph tool-using coder agent with modern best practices"""
    logger.info("=== CODER AGENT STARTED ===")

    from agent.tools import set_project_root
    from pathlib import Path
    
    # Get project root from state
    project_root_str = state.get("project_root")
    if project_root_str:
        set_project_root(Path(project_root_str))
        logger.info(f"Set project root from state: {project_root_str}")

    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)
        logger.info("Initialized new coder state")

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        logger.info("All implementation steps completed")
        logger.info("=== CODER AGENT COMPLETED ===")
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    logger.info(f"Processing step {coder_state.current_step_idx + 1}/{len(steps)}: {current_task.task_description}")
    logger.info(f"Target file: {current_task.filepath}")
    
    existing_content = read_file.run(current_task.filepath)
    logger.debug(f"Existing content length: {len(existing_content)} characters")

    # Determine file type and add relevant examples
    file_ext = current_task.filepath.split('.')[-1].lower()
    
    examples = ""
    if file_ext == "html":
        examples = """
═══════════════════════════════════════════════════════════════
MODERN HTML BEST PRACTICES & PATTERNS
═══════════════════════════════════════════════════════════════

STRUCTURE:
✓ Use semantic HTML5: <header>, <main>, <section>, <article>, <nav>, <footer>
✓ Proper document structure with meta tags
✓ Viewport meta for responsiveness: <meta name="viewport" content="width=device-width, initial-scale=1.0">
✓ UTF-8 charset: <meta charset="UTF-8">

MODERN HTML PATTERNS:
<!-- Clean, semantic structure -->
<header class="site-header">
  <nav class="nav-container">
    <a href="#" class="logo">Brand</a>
    <ul class="nav-menu">
      <li><a href="#home">Home</a></li>
    </ul>
  </nav>
</header>

<main class="main-content">
  <section class="hero-section">
    <div class="container">
      <h1 class="hero-title">Welcome</h1>
      <p class="hero-subtitle">Description</p>
      <button class="btn btn-primary">Get Started</button>
    </div>
  </section>
</main>

ACCESSIBILITY:
✓ Use semantic elements
✓ Include alt text for images
✓ ARIA labels for interactive elements
✓ Proper heading hierarchy (h1 → h2 → h3)

DATA ATTRIBUTES:
✓ Use data-* for JavaScript hooks: data-action="submit", data-id="123"
"""
    elif file_ext == "css":
        examples = """
═══════════════════════════════════════════════════════════════
MODERN CSS BEST PRACTICES & PATTERNS
═══════════════════════════════════════════════════════════════

CSS VARIABLES (Custom Properties) - BEAUTIFUL DESIGN SYSTEM:
:root {
  /* Colors - Rich & Vibrant Palette */
  --color-primary: #667eea;
  --color-secondary: #764ba2;
  --color-accent: #f093fb;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  
  /* Background - NO PLAIN WHITE! Use gradients or colors */
  --color-bg-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --color-bg-secondary: linear-gradient(to right, #f093fb 0%, #f5576c 100%);
  --color-bg-light: #f8fafc;
  --color-bg-card: rgba(255, 255, 255, 0.95);
  
  /* Text */
  --color-text: #1e293b;
  --color-text-light: #64748b;
  --color-text-inverse: #ffffff;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 2rem;
  --spacing-xl: 4rem;
  
  /* Typography */
  --font-base: 16px;
  --font-scale: 1.25;
  
  /* Effects - Premium Shadows */
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.12);
  --shadow-lg: 0 10px 40px rgba(0,0,0,0.16);
  --shadow-glow: 0 0 20px rgba(102, 126, 234, 0.4);
  
  /* Border Radius */
  --radius-sm: 6px;
  --radius: 12px;
  --radius-lg: 20px;
  
  /* Transitions */
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-fast: all 0.15s ease;
}

/* Beautiful Body Background */
body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  /* OR use a subtle pattern */
  /* background: #f8fafc url('data:image/svg+xml,...') repeat; */
  min-height: 100vh;
}

MODERN LAYOUT PATTERNS:
/* Flexbox centering */
.flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* CSS Grid layout */
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

/* Card component - Beautiful & Interactive */
.card {
  background: var(--color-bg-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  padding: var(--spacing-lg);
  transition: var(--transition);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: var(--shadow-lg);
}

MODERN EFFECTS:
/* Gradient backgrounds */
.gradient-bg {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
}

/* Glassmorphism */
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius);
}

/* Button styles - Premium & Interactive */
.btn {
  padding: 0.875rem 2rem;
  border: none;
  border-radius: var(--radius);
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  color: white;
  box-shadow: var(--shadow-md);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg), var(--shadow-glow);
}

.btn-primary:active {
  transform: translateY(0);
}

/* Button ripple effect */
.btn::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.btn:active::after {
  width: 300px;
  height: 300px;
}

RESPONSIVE DESIGN:
/* Mobile first approach */
.container {
  width: 100%;
  padding: 0 var(--spacing-md);
  margin: 0 auto;
}

/* Tablet */
@media (min-width: 640px) {
  .container { max-width: 640px; }
}

/* Desktop */
@media (min-width: 1024px) {
  .container { max-width: 1024px; }
  /* Add desktop-specific styles */
}

ANIMATIONS:
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fadeIn 0.6s ease-out;
}
"""
    elif file_ext == "js":
        examples = """
═══════════════════════════════════════════════════════════════
MODERN JAVASCRIPT BEST PRACTICES & PATTERNS
═══════════════════════════════════════════════════════════════

ES6+ FEATURES:
✓ Use const/let instead of var
✓ Arrow functions for cleaner syntax
✓ Destructuring for cleaner code
✓ Template literals for string interpolation
✓ Spread operator for arrays/objects

MODERN PATTERNS:

// DOM Selection (cache selectors)
const elements = {
  form: document.querySelector('#myForm'),
  input: document.querySelector('#myInput'),
  button: document.querySelector('#myButton'),
  display: document.querySelector('#display')
};

// Event Delegation (efficient for dynamic content)
document.addEventListener('click', (e) => {
  if (e.target.matches('.btn-delete')) {
    handleDelete(e.target.dataset.id);
  }
});

// Modern fetch with async/await
const fetchData = async (url) => {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Network error');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Fetch error:', error);
    showError('Failed to load data');
  }
};

// Debouncing for performance
const debounce = (func, delay = 300) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

// Usage
const handleSearch = debounce((query) => {
  console.log('Searching for:', query);
}, 300);

// Class-based component (optional)
class Calculator {
  constructor() {
    this.currentValue = 0;
    this.previousValue = 0;
    this.operation = null;
    this.init();
  }
  
  init() {
    this.bindEvents();
    this.updateDisplay();
  }
  
  bindEvents() {
    document.querySelectorAll('.btn-number').forEach(btn => {
      btn.addEventListener('click', () => this.handleNumber(btn.dataset.number));
    });
  }
  
  updateDisplay() {
    document.querySelector('#display').textContent = this.currentValue;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Your initialization code here
  console.log('App initialized');
});

ERROR HANDLING:
✓ Always use try-catch for async operations
✓ Provide user feedback for errors
✓ Log errors for debugging

USER FEEDBACK:
✓ Show loading states
✓ Display success/error messages
✓ Disable buttons during processing
✓ Validate input before processing

PERFORMANCE:
✓ Cache DOM queries
✓ Use event delegation
✓ Debounce/throttle expensive operations
✓ Avoid unnecessary re-renders
"""

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"═══════════════════════════════════════════════════════════════\n"
        f"IMPLEMENTATION TASK #{coder_state.current_step_idx + 1}\n"
        f"═══════════════════════════════════════════════════════════════\n\n"
        f"TASK DESCRIPTION:\n{current_task.task_description}\n\n"
        f"TARGET FILE: {current_task.filepath}\n\n"
        f"{examples}\n\n"
        f"EXISTING CONTENT:\n{existing_content if existing_content else '(Empty file - create from scratch)'}\n\n"
        f"═══════════════════════════════════════════════════════════════\n"
        f"CRITICAL REQUIREMENTS:\n"
        f"═══════════════════════════════════════════════════════════════\n"
        f"1. You MUST use write_file('{current_task.filepath}', content) to save your code\n"
        f"2. Write PRODUCTION-READY, MODERN, BEAUTIFUL code\n"
        f"3. Follow ALL best practices shown in the examples above\n"
        f"4. Make it visually stunning and professional\n"
        f"5. Ensure full functionality - no placeholders or TODOs\n"
        f"6. Use modern patterns, clean syntax, and proper structure\n\n"
        f"CREATE AMAZING CODE NOW! 🚀\n"
    )

    coder_tools = [read_file, write_file, list_files, get_current_directory]
    react_agent = create_react_agent(coder_llm, coder_tools)

    logger.info("Invoking React agent for code generation...")
    
    # Ensure project root is set before invoking React agent
    from agent.tools import get_project_root
    current_root = get_project_root()
    if current_root:
        logger.info(f"Project root confirmed: {current_root}")
    else:
        logger.warning("⚠ WARNING: Project root not set in coder_agent thread!")
    
    result = react_agent.invoke({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    })
    
    # Log the agent's response to see what happened
    if result and "messages" in result:
        last_message = result["messages"][-1]
        logger.info(f"Agent response: {last_message.content[:200]}...")
        
        # Check if write_file was actually called
        tool_calls = [msg for msg in result["messages"] if hasattr(msg, 'tool_calls') and msg.tool_calls]
        if tool_calls:
            logger.info(f"✓ Tools called: {len(tool_calls)} tool calls made")
            for msg in tool_calls:
                for tool_call in msg.tool_calls:
                    logger.info(f"  - Tool: {tool_call.get('name', 'unknown')}")
        else:
            logger.warning("⚠ WARNING: No tool calls detected - file may not have been written!")
    
    logger.info(f"Step {coder_state.current_step_idx + 1} completed")

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


def reviewer_agent(state: dict) -> dict:
    """Reviews generated code for quality and beauty"""
    logger.info("=== REVIEWER AGENT STARTED ===")
    
    from agent.tools import set_project_root
    from pathlib import Path
    
    # Set project root from state
    project_root_str = state.get("project_root")
    if project_root_str:
        set_project_root(Path(project_root_str))
        logger.info(f"Set project root for reviewer: {project_root_str}")
    
    coder_state = state.get("coder_state")
    if not coder_state:
        logger.info("No coder state found, skipping review")
        return {"review": "Skipped - no code to review"}
    
    task_plan = coder_state.task_plan
    
    # Read all generated files
    generated_files = {}
    for step in task_plan.implementation_steps:
        try:
            content = read_file.run(step.filepath)
            if content:
                generated_files[step.filepath] = content
                logger.info(f"✓ Read file for review: {step.filepath} ({len(content)} chars)")
        except Exception as e:
            logger.warning(f"Could not read {step.filepath}: {e}")
    
    if not generated_files:
        logger.info("No files generated to review")
        return {"review": "No files generated"}
    
    review_prompt = f"""
You are a senior code reviewer specializing in web development and UI/UX design.

Review the following generated website files:

{json.dumps({k: v[:500] + "..." if len(v) > 500 else v for k, v in generated_files.items()}, indent=2)}

REVIEW CRITERIA:

1. VISUAL DESIGN & AESTHETICS:
   - Is it modern and professional?
   - Good use of colors, spacing, typography?
   - Visual hierarchy clear?
   - Overall "wow factor"?

2. CODE QUALITY:
   - Modern best practices followed?
   - Clean, readable, maintainable?
   - Proper structure and organization?
   - No obvious bugs or issues?

3. RESPONSIVENESS:
   - Mobile-friendly design?
   - Proper breakpoints?
   - Flexible layouts?

4. FUNCTIONALITY:
   - All features implemented?
   - JavaScript working correctly?
   - Forms and interactions functional?

5. ACCESSIBILITY:
   - Semantic HTML?
   - Proper ARIA labels?
   - Keyboard navigation?

Provide:
- Overall quality score (1-10)
- What's great about it
- What could be improved
- Specific actionable suggestions

Keep it concise but actionable.
"""
    
    review_response = reviewer_llm.invoke(review_prompt)
    review_content = review_response.content
    
    logger.info("=== CODE REVIEW RESULTS ===")
    logger.info(review_content)
    logger.info("=== REVIEWER AGENT COMPLETED ===")
    
    return {"review": review_content}


# Build the LangGraph
graph = StateGraph(dict)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)
graph.add_node("reviewer", reviewer_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "reviewer" if s.get("status") == "DONE" else "coder",
    {"reviewer": "reviewer", "coder": "coder"}
)
graph.add_edge("reviewer", END)

graph.set_entry_point("planner")

# Compile the agent
agent = graph.compile()

logger.info("Enhanced LangGraph agent compiled and ready")
logger.info("Features: Design-focused planning, modern best practices, code review")