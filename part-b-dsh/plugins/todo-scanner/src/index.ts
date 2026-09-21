import { defineTool } from "@deepseek-ai/dsh-tools";
import fs from "node:fs/promises";
import path from "node:path";

/** Cordis plugin name used by loader diagnostics. */
export const name = "todo-scanner";

/** Services required by the todo scanner tool. */
export const inject = ["tools", "systemPrompt"];

/**
 * Recursively scan directories for TODO/FIXME comments, skipping excluded directories.
 * @param dirPath - The directory path to scan
 * @param excludedDirs - Set of directory names to skip
 * @returns Array of matches with file path, line number, and text
 */
async function scanTodosRecursive(dirPath: string, excludedDirs: Set<string>): Promise<Array<{ filePath: string; lineNumber: number; text: string }>> {
  const results: Array<{ filePath: string; lineNumber: number; text: string }> = [];
  
  async function scanDirectory(currentPath: string): Promise<void> {
    try {
      const entries = await fs.readdir(currentPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(currentPath, entry.name);
        
        if (entry.isDirectory()) {
          // Skip excluded directories
          if (excludedDirs.has(entry.name)) {
            continue;
          }
          await scanDirectory(fullPath);
        } else if (entry.isFile()) {
          // Only scan text files (skip binary files)
          const ext = path.extname(entry.name).toLowerCase();
          const isTextFile = [
            '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs',
            '.py', '.rb', '.go', '.rs', '.java', '.c', '.cpp', '.h',
            '.cs', '.kt', '.swift', '.php', '.sh', '.bash', '.zsh',
            '.yaml', '.yml', '.toml', '.ini', '.md', '.markdown', '.mdx',
            '.html', '.htm', '.css', '.scss', '.less', '.sql', '.xml', '.lua',
            '.txt', '.json', '.jsonc'
          ].includes(ext);
          
          if (isTextFile) {
            try {
              const content = await fs.readFile(fullPath, 'utf8');
              const lines = content.split('\n');
              
              for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const lineNumber = i + 1;
                
                // Look for TODO: or FIXME: comments (case-insensitive)
                const todoMatch = line.match(/TODO:\s*(.+)/i);
                const fixmeMatch = line.match(/FIXME:\s*(.+)/i);
                
                if (todoMatch) {
                  results.push({
                    filePath: fullPath,
                    lineNumber,
                    text: todoMatch[0].trim()
                  });
                }
                
                if (fixmeMatch) {
                  results.push({
                    filePath: fullPath,
                    lineNumber,
                    text: fixmeMatch[0].trim()
                  });
                }
              }
            } catch (error) {
              // Skip files that can't be read (permissions, etc.)
              continue;
            }
          }
        }
      }
    } catch (error) {
      // Skip directories that can't be accessed
      return;
    }
  }
  
  await scanDirectory(dirPath);
  return results;
}

/** Register the todo scanner plugin. */
export function apply(ctx: any) {
  // Add system prompt guidance
  ctx.systemPrompt.section({
    name: "tool:scan_todos",
    order: 1550,
    text: ({ scope }) => ctx.tools.get("scan_todos", scope) === void 0 ? "" : "Use the scan_todos tool to recursively scan the workspace for TODO: and FIXME: comments. It returns each match's file path, line number, and text."
  });
  
  // Register the scan_todos tool
  ctx.tools.register(defineTool({
    name: "scan_todos",
    description: "Recursively scan the workspace for TODO: and FIXME: comments and return each match's file path, line number, and text.",
    parameters: {
      path: {
        type: "string",
        description: "Optional path to scan (defaults to current working directory). Resolved against process.cwd().",
        default: "."
      }
    },
    output: {
      schema: {
        type: "object",
        additionalProperties: false,
        properties: {
          matches: {
            type: "array",
            required: true,
            items: {
              type: "object",
              additionalProperties: false,
              properties: {
                filePath: {
                  type: "string",
                  required: true
                },
                lineNumber: {
                  type: "integer",
                  required: true
                },
                text: {
                  type: "string",
                  required: true
                }
              }
            }
          },
          summary: {
            type: "string",
            required: true
          }
        }
      },
      render: (_args, value) => {
        if (value.matches.length === 0) {
          return [{
            type: "text",
            text: "No TODO/FIXME comments found."
          }];
        }
        
        const matchLines = value.matches.map(match => 
          `${match.filePath}:${match.lineNumber}: ${match.text}`
        );
        
        return [{
          type: "text",
          text: `${value.summary}\n\n${matchLines.join('\n')}`
        }];
      },
      presentationMeta: (_args, value) => ({
        matches: value.matches,
        summary: value.summary
      })
    },
    isConcurrencySafe: () => true,
    async execute(args, exec) {
      const scanPath = args.path ?? ".";
      const resolvedPath = path.resolve(process.cwd(), scanPath);
      
      // Check if the path exists
      try {
        const stat = await fs.stat(resolvedPath);
        if (!stat.isDirectory()) {
          throw new Error(`Path "${resolvedPath}" is not a directory`);
        }
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
          throw new Error(`Path "${resolvedPath}" does not exist`);
        }
        throw error;
      }
      
      // Set of directories to skip
      const excludedDirs = new Set(['node_modules', '.git', '.dsh-home', 'dist', 'build']);
      
      // Scan for TODO/FIXME comments
      const matches = await scanTodosRecursive(resolvedPath, excludedDirs);
      
      // Create summary
      const todoCount = matches.filter(m => m.text.toUpperCase().startsWith('TODO')).length;
      const fixmeCount = matches.filter(m => m.text.toUpperCase().startsWith('FIXME')).length;
      
      const summary = matches.length === 0 
        ? 'No TODO/FIXME comments found.' 
        : `Found ${matches.length} TODO/FIXME comment${matches.length === 1 ? '' : 's'} (${todoCount} TODO, ${fixmeCount} FIXME) in ${resolvedPath}`;
      
      return {
        matches,
        summary
      };
    },
    presentCall(args) {
      const scanPath = args.path ?? ".";
      return {
        card: "generic",
        title: `Scan TODO/FIXME comments${scanPath !== "." ? ` in ${scanPath}` : ""}`,
        kind: "scan"
      };
    },
    presentResult(_args, result) {
      if (result.isError) return undefined;
      
      const meta = result.meta as { matches?: Array<{ filePath: string; lineNumber: number; text: string }>, summary?: string };
      if (!meta || !meta.matches || !meta.summary) return undefined;
      
      if (meta.matches.length === 0) {
        return {
          card: "generic",
          title: "No TODO/FIXME comments found",
          content: result.content
        };
      }
      
      const todoCount = meta.matches.filter(m => m.text.toUpperCase().startsWith('TODO')).length;
      const fixmeCount = meta.matches.filter(m => m.text.toUpperCase().startsWith('FIXME')).length;
      
      return {
        card: "scan",
        title: meta.summary,
        matches: meta.matches,
        counts: {
          total: meta.matches.length,
          todo: todoCount,
          fixme: fixmeCount
        },
        content: result.content
      };
    }
  }));
}