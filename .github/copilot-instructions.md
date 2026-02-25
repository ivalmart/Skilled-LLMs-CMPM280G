# Copilot Custom Instructions: Procgen Solution Prototyping

# Before You Do This
Read this website: https://www.pcgbook.com/

## Purpose
Enable rapid prototyping of multiple algorithmic solutions to procedural generation (procgen) problems and render their outputs in HTML for easy comparison and visualization.

## Instructions

1. **Procgen Problem Definition**
   - Accept a clear description of the procedural generation problem (e.g., maze generation, terrain generation, random art, etc.).

2. **Solution Prototyping**
   - Implement multiple distinct algorithmic solutions to the problem, each as a separate function or class.
   - Each solution should be self-contained and parameterizable.
   - Solutions should be easy to extend or modify.

3. **HTML Rendering**
   - For each solution, generate an HTML representation of its output.
   - Use inline SVG, HTML5 canvas, or preformatted text as appropriate for the problem domain.
   - Display all solutions side-by-side or in a grid for easy visual comparison.
   - Include solution names and brief descriptions above each rendered output.

4. **Extensibility**
   - Make it easy to add new solutions by following a clear interface or template.
   - Document how to add new solutions and rendering methods.

5. **Usage**
   - The script or module should be runnable as a standalone file, generating an HTML file as output.
   - Optionally, support command-line arguments to select the problem, number of solutions, or output file name.

## Example Workflow
1. User describes a procgen problem (e.g., "generate a 10x10 maze").
2. The script implements and runs several maze generation algorithms (e.g., DFS, Prim's, Kruskal's).
3. The script renders each maze as SVG in an HTML file, labeling each with the algorithm used.
4. The user opens the HTML file to compare the results visually.

---

**Note:**
- Focus on clarity, modularity, and ease of extension.
- Prefer pure Python and standard libraries unless a specific library is required for rendering.
- Document all solution prototypes and rendering logic clearly.
