import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import random
import time
from collections import defaultdict
import threading
import math

# Mock crossword classes - replace with your actual imports
class Variable:
    def __init__(self, i, j, direction, length):
        self.i = i
        self.j = j
        self.direction = direction
        self.length = length
        self.cells = []
        
        # Generate cells based on direction
        if direction == 0:  # ACROSS
            self.cells = [(i, j + k) for k in range(length)]
        else:  # DOWN
            self.cells = [(i + k, j) for k in range(length)]

class Crossword:
    def __init__(self, structure_file=None, words_file=None, structure_text=None, words_text=None):
        self.height = 0
        self.width = 0
        self.structure = []
        self.variables = set()
        self.words = set()
        self.overlaps = {}
        
        # Load structure
        if structure_file:
            self.load_structure_from_file(structure_file)
        elif structure_text:
            self.load_structure_from_text(structure_text)
            
        # Load words
        if words_file:
            self.load_words_from_file(words_file)
        elif words_text:
            self.load_words_from_text(words_text)
            
        # Find variables
        self.find_variables()
        # Calculate overlaps
        self.calculate_overlaps()
    
    def load_structure_from_file(self, filename):
        """Load crossword structure from file"""
        try:
            with open(filename, 'r') as f:
                content = f.read().strip()
                self.load_structure_from_text(content)
        except Exception as e:
            raise Exception(f"Error loading structure file: {e}")
    
    def load_structure_from_text(self, content):
        """Load crossword structure from text"""
        try:
            lines = content.strip().split('\n')
            self.height = len(lines)
            self.width = len(lines[0]) if lines else 0
            
            self.structure = []
            for line in lines:
                row = []
                for char in line:
                    # True for empty cells (_), False for blocked cells (#)
                    row.append(char == '_')
                self.structure.append(row)
        except Exception as e:
            raise Exception(f"Error parsing structure: {e}")
    
    def load_words_from_file(self, filename):
        """Load words from file"""
        try:
            with open(filename, 'r') as f:
                content = f.read()
                self.load_words_from_text(content)
        except Exception as e:
            raise Exception(f"Error loading words file: {e}")
    
    def load_words_from_text(self, content):
        """Load words from text"""
        try:
            self.words = set()
            for line in content.split('\n'):
                word = line.strip().upper()
                if word and word.isalpha():
                    self.words.add(word)
        except Exception as e:
            raise Exception(f"Error parsing words: {e}")
    
    def find_variables(self):
        """Find all possible word positions in the crossword"""
        self.variables = set()
        
        # Find horizontal variables (ACROSS)
        for i in range(self.height):
            j = 0
            while j < self.width:
                if self.structure[i][j]:
                    # Start of a potential word
                    start_j = j
                    length = 0
                    while j < self.width and self.structure[i][j]:
                        length += 1
                        j += 1
                    
                    # Add variable if length >= 2
                    if length >= 2:
                        var = Variable(i, start_j, 0, length)  # 0 = ACROSS
                        self.variables.add(var)
                else:
                    j += 1
        
        # Find vertical variables (DOWN)
        for j in range(self.width):
            i = 0
            while i < self.height:
                if self.structure[i][j]:
                    # Start of a potential word
                    start_i = i
                    length = 0
                    while i < self.height and self.structure[i][j]:
                        length += 1
                        i += 1
                    
                    # Add variable if length >= 2
                    if length >= 2:
                        var = Variable(start_i, j, 1, length)  # 1 = DOWN
                        self.variables.add(var)
                else:
                    i += 1
    
    def calculate_overlaps(self):
        """Calculate overlaps between variables"""
        self.overlaps = {}
        variables_list = list(self.variables)
        
        for i, var1 in enumerate(variables_list):
            for j, var2 in enumerate(variables_list):
                if i != j:
                    overlap = None
                    
                    # Find intersection point
                    for idx1, cell1 in enumerate(var1.cells):
                        for idx2, cell2 in enumerate(var2.cells):
                            if cell1 == cell2:
                                overlap = (idx1, idx2)
                                break
                        if overlap:
                            break
                    
                    self.overlaps[(var1, var2)] = overlap

class CrosswordCreator:
    def __init__(self, crossword):
        self.crossword = crossword
        self.domains = {}
        
        # Initialize domains
        for variable in crossword.variables:
            self.domains[variable] = [word for word in crossword.words if len(word) == variable.length]
    
    def solve(self):
        """Solve the crossword using backtracking"""
        assignment = {}
        if self.backtrack(assignment):
            return assignment
        return None
    
    def backtrack(self, assignment):
        """Backtracking search"""
        if len(assignment) == len(self.crossword.variables):
            return True
        
        # Select unassigned variable
        var = self.select_unassigned_variable(assignment)
        
        for word in self.order_domain_values(var, assignment):
            if self.consistent(var, word, assignment):
                assignment[var] = word
                
                if self.backtrack(assignment):
                    return True
                
                del assignment[var]
        
        return False
    
    def select_unassigned_variable(self, assignment):
        """Select next variable to assign"""
        unassigned = [v for v in self.crossword.variables if v not in assignment]
        return unassigned[0] if unassigned else None
    
    def order_domain_values(self, var, assignment):
        """Order domain values"""
        return self.domains[var]
    
    def consistent(self, var, value, assignment):
        """Check if assignment is consistent"""
        for other_var, other_value in assignment.items():
            if var != other_var:
                overlap = self.crossword.overlaps.get((var, other_var))
                if overlap:
                    i, j = overlap
                    if i < len(value) and j < len(other_value):
                        if value[i] != other_value[j]:
                            return False
        return True
    
    def letter_grid(self, assignment):
        """Create letter grid from assignment"""
        grid = [[None for _ in range(self.crossword.width)] for _ in range(self.crossword.height)]
        
        for variable, word in assignment.items():
            for idx, (i, j) in enumerate(variable.cells):
                if 0 <= i < self.crossword.height and 0 <= j < self.crossword.width:
                    grid[i][j] = word[idx]
        
        return grid

class CrosswordGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Crossword Puzzle Generator")
        self.master.geometry("1200x800")
        
        # Initialize variables
        self.assignment = None
        self.crossword = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Create main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="10")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        # Structure input
        ttk.Label(input_frame, text="Structure:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Label(input_frame, text="(Use '_' for empty cells, '#' for blocked cells)").grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        
        self.structure_text = tk.Text(input_frame, height=8, width=50)
        self.structure_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        structure_scroll = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.structure_text.yview)
        structure_scroll.grid(row=1, column=2, sticky=(tk.N, tk.S), pady=(0, 10))
        self.structure_text.config(yscrollcommand=structure_scroll.set)
        
        # Words input
        ttk.Label(input_frame, text="Words:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Label(input_frame, text="(One word per line)").grid(row=2, column=1, sticky=tk.W, pady=(0, 5))
        
        self.words_text = tk.Text(input_frame, height=8, width=50)
        self.words_text.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        words_scroll = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.words_text.yview)
        words_scroll.grid(row=3, column=2, sticky=(tk.N, tk.S), pady=(0, 10))
        self.words_text.config(yscrollcommand=words_scroll.set)
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons
        ttk.Button(control_frame, text="Load Structure File", 
                  command=self.load_structure_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Load Words File", 
                  command=self.load_words_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Generate Crossword", 
                  command=self.generate_crossword).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Clear Canvas", 
                  command=self.clear_canvas).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Clear All", 
                  command=self.clear_all).pack(side=tk.LEFT, padx=(0, 5))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Enter structure and words, then click Generate Crossword")
        self.status_label.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Canvas with scrollbars
        canvas_frame = ttk.LabelFrame(main_frame, text="Crossword", padding="5")
        canvas_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(canvas_frame, width=800, height=400, bg="white")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid scrollbars and canvas
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Add sample data
        self.add_sample_data()
    
    def add_sample_data(self):
        """Add sample data to help users understand the format"""
        sample_structure = """#___#
#_##_
#_##_
#_##_
#____"""
        
        sample_words = """one
two
three
four
five
six
seven
eight
nine
ten"""
        
        self.structure_text.insert(tk.END, sample_structure)
        self.words_text.insert(tk.END, sample_words)
    
    def load_structure_file(self):
        """Load structure from file"""
        filename = filedialog.askopenfilename(
            title="Select Structure File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                self.structure_text.delete(1.0, tk.END)
                self.structure_text.insert(1.0, content)
                self.status_label.config(text=f"Structure loaded: {os.path.basename(filename)}")
                messagebox.showinfo("Success", f"Structure file loaded: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load structure file: {str(e)}")
    
    def load_words_file(self):
        """Load words from file"""
        filename = filedialog.askopenfilename(
            title="Select Words File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                self.words_text.delete(1.0, tk.END)
                self.words_text.insert(1.0, content)
                self.status_label.config(text=f"Words loaded: {os.path.basename(filename)}")
                messagebox.showinfo("Success", f"Words file loaded: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load words file: {str(e)}")
    
    def generate_crossword(self):
        """Generate crossword puzzle"""
        structure_content = self.structure_text.get(1.0, tk.END).strip()
        words_content = self.words_text.get(1.0, tk.END).strip()
        
        if not structure_content or not words_content:
            messagebox.showerror("Error", "Please enter both structure and words.")
            return
        
        try:
            self.status_label.config(text="Generating crossword...")
            self.master.update()
            
            # Create crossword
            self.crossword = Crossword(structure_text=structure_content, words_text=words_content)
            
            if not self.crossword.variables:
                messagebox.showerror("Error", "No valid word positions found in the structure.")
                self.status_label.config(text="No valid word positions found")
                return
            
            if not self.crossword.words:
                messagebox.showerror("Error", "No valid words found in the word list.")
                self.status_label.config(text="No valid words found")
                return
            
            # Create solver
            creator = CrosswordCreator(self.crossword)
            
            # Solve
            self.assignment = creator.solve()
            
            if self.assignment:
                self.status_label.config(text="Crossword generated successfully!")
                self.draw_crossword()
                messagebox.showinfo("Success", "Crossword generated successfully!")
            else:
                self.status_label.config(text="Failed to generate crossword")
                messagebox.showerror("Error", "Could not generate a valid crossword with the given words. Try adding more words or simplifying the structure.")
                
        except Exception as e:
            self.status_label.config(text="Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def draw_crossword(self):
        """Draw the crossword on canvas"""
        if not self.crossword or not self.assignment:
            return
        
        self.canvas.delete("all")
        
        cell_size = 40
        border_width = 2
        
        # Calculate canvas size
        canvas_width = self.crossword.width * cell_size + 20
        canvas_height = self.crossword.height * cell_size + 20
        
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Get letter grid
        creator = CrosswordCreator(self.crossword)
        letters = creator.letter_grid(self.assignment)
        
        # Draw grid
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                x0 = j * cell_size + 10
                y0 = i * cell_size + 10
                x1 = x0 + cell_size
                y1 = y0 + cell_size
                
                if self.crossword.structure[i][j]:
                    # White cell (open space)
                    self.canvas.create_rectangle(x0, y0, x1, y1, 
                                               fill="white", outline="black", width=border_width)
                    
                    # Add letter if exists
                    if letters[i][j]:
                        self.canvas.create_text(x0 + cell_size//2, y0 + cell_size//2, 
                                              text=letters[i][j], 
                                              font=("Arial", 16, "bold"), 
                                              fill="black")
                else:
                    # Black cell (blocked)
                    self.canvas.create_rectangle(x0, y0, x1, y1, 
                                               fill="gray", outline="darkgray")
        
        # Add word numbers (optional)
        self.add_word_numbers(cell_size)
    
    def add_word_numbers(self, cell_size):
        """Add numbers to starting positions of words"""
        word_num = 1
        numbered_cells = set()
        
        for variable in self.crossword.variables:
            start_i, start_j = variable.cells[0]
            
            if (start_i, start_j) not in numbered_cells:
                x = start_j * cell_size + 10 + 5
                y = start_i * cell_size + 10 + 5
                
                self.canvas.create_text(x, y, text=str(word_num), 
                                      font=("Arial", 8, "bold"), 
                                      fill="blue", anchor="nw")
                
                numbered_cells.add((start_i, start_j))
                word_num += 1
    
    def clear_canvas(self):
        """Clear the canvas"""
        self.canvas.delete("all")
        self.status_label.config(text="Canvas cleared")
    
    def clear_all(self):
        """Clear everything"""
        self.canvas.delete("all")
        self.structure_text.delete(1.0, tk.END)
        self.words_text.delete(1.0, tk.END)
        self.assignment = None
        self.crossword = None
        self.status_label.config(text="All cleared. Enter structure and words to begin.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CrosswordGUI(root)
    root.mainloop()
