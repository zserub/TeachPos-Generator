class Position:
    def __init__(self, name, tool, base, number):
        self.name = name
        self.tool = tool
        self.base = base
        self.number = number

    def __str__(self):
        return f"Position: {self.name} - Tool: {self.tool} - Base: {self.base} - Number: {self.number}"


class Folder:
    def __init__(self, name):
        self.name = name
        self.positions = []
        self.subfolders = {}

    def add_position(self, position):
        self.positions.append(position)

    def add_subfolder(self, folder):
        self.subfolders[folder.name] = folder

    def __str__(self):
        folder_str = f"Folder: {self.name}\n"
        for position in self.positions:
            folder_str += str(position) + "\n"
        for subfolder in self.subfolders.values():
            folder_str += str(subfolder) + "\n"
        return folder_str


class FolderHierarchy:
    def __init__(self):
        self.root_folder = Folder("root")

    def add_folder(self, folder_name, parent_folder_name=None):
        new_folder = Folder(folder_name)
        if parent_folder_name:
            parent_folder = self._find_folder(self.root_folder, parent_folder_name)
            if parent_folder:
                parent_folder.add_subfolder(new_folder)
            else:
                print(f"Parent folder '{parent_folder_name}' not found.")
        else:
            self.root_folder.add_subfolder(new_folder)

    def add_position_to_folder(self, folder_name, position):
        folder = self._find_folder(self.root_folder, folder_name)
        if folder:
            folder.add_position(position)
        else:
            print(f"Folder '{folder_name}' does not exist.")

    def _find_folder(self, start_folder, folder_name):
        if start_folder.name == folder_name:
            return start_folder
        for subfolder in start_folder.subfolders.values():
            found_folder = self._find_folder(subfolder, folder_name)
            if found_folder:
                return found_folder
        return None

    def __str__(self):
        return str(self.root_folder)


# Example usage:
folder_hierarchy = FolderHierarchy()

# Adding folders
folder_hierarchy.add_folder("joints")
folder_hierarchy.add_folder("descartes")
folder_hierarchy.add_folder("TYPE1", parent_folder_name="descartes")

# Creating positions
positions = [
    Position("J_Home", 1, 1, 1),
    Position("J_Service", 1, 1, 2),
    Position("J_Corner_1", 1, 1, 3),
    Position("P_Pick_PCB_T1", 1, 1, 4),
    Position("P_Place_PCB_T1", 1, 1, 5)
]

# Adding positions to folders
folder_hierarchy.add_position_to_folder("joints", positions[0])
folder_hierarchy.add_position_to_folder("joints", positions[1])
folder_hierarchy.add_position_to_folder("joints", positions[2])
folder_hierarchy.add_position_to_folder("TYPE1", positions[3])
folder_hierarchy.add_position_to_folder("TYPE1", positions[4])

# Printing folder hierarchy
print(folder_hierarchy)