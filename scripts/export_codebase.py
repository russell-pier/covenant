#!/usr/bin/env python3
"""
Script to export an entire codebase to a markdown file.
Recursively walks through directories and includes all code files.
"""

import os
import argparse
from pathlib import Path

# Common code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj',
    '.sh', '.bash', '.zsh', '.ps1', '.sql', '.r', '.m', '.pl', '.lua',
    '.dart', '.elm', '.ex', '.exs', '.fs', '.fsx', '.hs', '.jl', '.nim',
    '.ml', '.mli', '.pas', '.pp', '.pro', '.v', '.vhd', '.vhdl', '.sv',
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.xml', '.json',
    '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.md', '.txt',
    '.dockerfile', '.makefile', '.cmake', '.gradle', '.maven', '.sbt'
}

# Files and directories to ignore
IGNORE_PATTERNS = {
    '__pycache__', '.git', '.svn', '.hg', 'node_modules', '.env', 'venv',
    'env', '.venv', 'dist', 'build', '.idea', '.vscode', '.vs', 'target',
    'bin', 'obj', '.gradle', '.maven', 'vendor', 'logs', 'log', 'tmp',
    'temp', '.DS_Store', 'Thumbs.db', '.pytest_cache', '.coverage',
    '.mypy_cache', '.tox', '.nox', '.eggs', '*.egg-info', '.cache'
}

def should_ignore(path):
    """Check if a file or directory should be ignored."""
    name = os.path.basename(path)
    
    # Check against ignore patterns
    for pattern in IGNORE_PATTERNS:
        if pattern.startswith('*'):
            if name.endswith(pattern[1:]):
                return True
        elif pattern in name or name == pattern:
            return True
    
    return False

def is_code_file(file_path):
    """Check if a file is a code file based on its extension."""
    ext = Path(file_path).suffix.lower()
    
    # Special cases for files without extensions
    name = os.path.basename(file_path).lower()
    if name in ['dockerfile', 'makefile', 'vagrantfile', 'jenkinsfile']:
        return True
    
    return ext in CODE_EXTENSIONS

def get_language_from_extension(file_path):
    """Get the language identifier for markdown code blocks."""
    ext = Path(file_path).suffix.lower()
    name = os.path.basename(file_path).lower()
    
    # Special cases
    if name in ['dockerfile']:
        return 'dockerfile'
    if name in ['makefile']:
        return 'makefile'
    
    # Extension mappings
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.clj': 'clojure',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.ps1': 'powershell',
        '.sql': 'sql',
        '.r': 'r',
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'ini',
        '.md': 'markdown',
        '.txt': 'text'
    }
    
    return lang_map.get(ext, 'text')

def read_file_safely(file_path):
    """Safely read a file, handling various encodings."""
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    return "Unable to decode file with common encodings"

def export_codebase(root_dir, output_file, max_file_size=50000):
    """Export codebase to markdown file."""
    root_path = Path(root_dir).resolve()
    files_processed = 0
    files_skipped = 0
    
    with open(output_file, 'w', encoding='utf-8') as md_file:
        # Write header
        md_file.write(f"# Codebase Export: {root_path.name}\n\n")
        md_file.write(f"Generated from: `{root_path}`\n\n")
        md_file.write("---\n\n")
        
        # Walk through directory tree
        for root, dirs, files in os.walk(root_path):
            # Remove ignored directories from dirs list to prevent traversal
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
            
            for file in sorted(files):
                file_path = os.path.join(root, file)
                
                # Skip ignored files
                if should_ignore(file_path):
                    continue
                
                # Only process code files
                if not is_code_file(file_path):
                    continue
                
                # Get relative path from root directory
                rel_path = os.path.relpath(file_path, root_path)
                
                # Check file size
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > max_file_size:
                        md_file.write(f"## {rel_path}\n\n")
                        md_file.write(f"*File too large ({file_size} bytes) - skipped*\n\n")
                        files_skipped += 1
                        continue
                except OSError:
                    continue
                
                # Read and write file content
                content = read_file_safely(file_path)
                language = get_language_from_extension(file_path)
                
                md_file.write(f"## {rel_path}\n\n")
                md_file.write(f"```{language}\n")
                md_file.write(content)
                if not content.endswith('\n'):
                    md_file.write('\n')
                md_file.write("```\n\n")
                
                files_processed += 1
        
        # Write summary
        md_file.write("---\n\n")
        md_file.write(f"**Export Summary:**\n")
        md_file.write(f"- Files processed: {files_processed}\n")
        md_file.write(f"- Files skipped: {files_skipped}\n")
    
    return files_processed, files_skipped

def main():
    parser = argparse.ArgumentParser(description='Export codebase to markdown file')
    parser.add_argument('directory', help='Root directory to scan')
    parser.add_argument('-o', '--output', default='codebase_export.md', 
                       help='Output markdown file (default: codebase_export.md)')
    parser.add_argument('--max-size', type=int, default=50000,
                       help='Maximum file size in bytes to include (default: 50000)')
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory")
        return 1
    
    try:
        files_processed, files_skipped = export_codebase(
            args.directory, 
            args.output, 
            args.max_size
        )
        
        print(f"✅ Export complete!")
        print(f"📁 Scanned directory: {os.path.abspath(args.directory)}")
        print(f"📄 Output file: {os.path.abspath(args.output)}")
        print(f"🔢 Files processed: {files_processed}")
        if files_skipped > 0:
            print(f"⚠️  Files skipped: {files_skipped}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())