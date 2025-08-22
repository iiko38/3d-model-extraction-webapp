#!/usr/bin/env python3
"""
Debug the database contents
"""

import sqlite3
import sys

def main():
    DB = sys.argv[1] if len(sys.argv) > 1 else "library/index.sqlite"
    
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    # Check for files with unusual file_type values
    cur.execute("""
        SELECT file_type, COUNT(*) 
        FROM files 
        WHERE file_type NOT IN ('revit', 'sketchup', 'autocad', 'autocad_3d', 'obj', 'fbx', 'glb', 'gltf', '3ds', '3dm', 'sif')
        GROUP BY file_type 
        ORDER BY COUNT(*) DESC;
    """)
    
    unusual_types = cur.fetchall()
    print("Files with unusual file_type values:")
    for file_type, count in unusual_types:
        print(f"  {file_type}: {count}")
    
    # Show a few examples of these files
    if unusual_types:
        print("\nExamples of files with unusual file_type:")
        cur.execute("""
            SELECT file_type, stored_path, ext 
            FROM files 
            WHERE file_type NOT IN ('revit', 'sketchup', 'autocad', 'autocad_3d', 'obj', 'fbx', 'glb', 'gltf', '3ds', '3dm', 'sif')
            LIMIT 5;
        """)
        
        examples = cur.fetchall()
        for file_type, stored_path, ext in examples:
            print(f"  {file_type} ({ext}): {stored_path}")
    
    con.close()

if __name__ == "__main__":
    main()
