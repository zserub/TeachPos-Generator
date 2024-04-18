import sys
import csv
import re

csv_file_path = './pos.csv'
out_pos = ''
out_dat = ''


class Position:
    def __init__(self, name, tool, base, number):
        self.name = name
        self.tool = tool
        self.base = base
        self.number = number

    def __str__(self):
        return f"Position: {self.name} - Tool: {self.tool} - Base: {self.base} - Number: {self.number}"


class Fold:
    def __init__(self, name):
        self.name = name
        self.positions = []
        self.subfolds = {}

    def add_position(self, position):
        self.positions.append(position)

    def add_subfold(self, fold):
        self.subfolds[fold.name] = fold

    def __str__(self):
        fold_str = f"fold: {self.name}\n"
        for position in self.positions:
            fold_str += str(position) + "\n"
        for subfold in self.subfolds.values():
            fold_str += str(subfold) + "\n"
        return fold_str


class FoldHierarchy:
    def __init__(self):
        self.root_fold = Fold("root")

    def add_fold(self, fold_name, parent_fold_name=None):
        # Check if the fold name already exists
        if self._find_fold(self.root_fold, fold_name):
            print(f"Fold '{fold_name}' already exists.")
            return

        new_fold = Fold(fold_name)
        if parent_fold_name:
            parent_fold = self._find_fold(self.root_fold, parent_fold_name)
            if parent_fold:
                parent_fold.add_subfold(new_fold)
            else:
                print(f"Parent fold '{parent_fold_name}' not found.")
        else:
            self.root_fold.add_subfold(new_fold)

    def add_position_to_fold(self, fold_name, position):
        fold = self._find_fold(self.root_fold, fold_name)
        if fold:
            fold.add_position(position)
        else:
            print(f"fold '{fold_name}' does not exist.")

    def _find_fold(self, start_fold, fold_name):
        if start_fold.name == fold_name:
            return start_fold
        for subfold in start_fold.subfolds.values():
            found_fold = self._find_fold(subfold, fold_name)
            if found_fold:
                return found_fold
        return None

    def __str__(self):
        return str(self.root_fold)

# class Duplication(Exception):
#     def __init__(self, message):
#         self.message = message
#         super().__init__(self.message)

#     def __str__(self):
#         return f"Error: {self.message}"


def process_csv(in_data, in_fold_count):
    number = 0

    for row in in_data[1:]:
        name = row[header_map['name']].strip()
        tool = int(row[header_map['tool']].strip())
        base = int(row[header_map['base']].strip())
        number += 1

        position = Position(name, tool, base, number)

        fold_names = [
            row[header_map[f'fold{i+1}']].strip() for i in range(in_fold_count)]

        if in_fold_count == 0:
            fold_hierarchy.add_position_to_fold("root", position)
        else:
            if not fold_names[0]:
                raise Exception(
                    'Error: Invalid csv structure; No fold name in first column.')

            foldname = ''
            for i, current_fold in enumerate(fold_names):
                if current_fold:
                    if i == 0:
                        fold_hierarchy.add_fold(current_fold)
                    else:
                        fold_hierarchy.add_fold(current_fold, fold_names[i-1])
                    foldname = current_fold
                else:
                    for prev_fold_name in reversed(fold_names[:i]):
                        if prev_fold_name:
                            # fold_hierarchy.add_position_to_fold(prev_fold_name, position)
                            foldname = prev_fold_name
                            break

            fold_hierarchy.add_position_to_fold(foldname, position)


# Check the header to define the structure of fold hierarchy
def process_header(headers):
    # Check if csv structure is correct
    for item in headers:
        if not re.match(r'(fold|name|tool|base)', item, re.IGNORECASE):
            raise Exception(
                f'Error: Invalid csv structure; unknown column: {item}')
    if 'name' not in (item.lower() for item in headers):
        raise Exception('Error: Invalid csv structure; missing "name" column.')
    if 'tool' not in [item.lower() for item in headers]:
        raise Exception('Error: Invalid csv structure; missing "tool" column.')
    if 'base' not in [item.lower() for item in headers]:
        raise Exception('Error: Invalid csv structure; missing "base" column.')

    # Count the number of folds
    count_fold = sum(1 for column in headers
                     if re.match('FOLD', column, re.IGNORECASE))
    print(f"Number of folds: {count_fold}")

    numbering = 1
    for index, header in enumerate(headers):
        if count_fold > 0:
            if re.match('FOLD', header, re.IGNORECASE):
                key = 'fold' + str(numbering)
                header_map[key] = index
                numbering += 1
            else:
                header_map[header.strip().lower()] = index
    return count_fold


def recognise_type(in_name):

    if in_name[:1] == "X":
        in_name = in_name[1:]

    if in_name in pos_type_dict:
        print(f"Error: Duplicate POS name '{in_name}'")
        sys.exit()
    if len(in_name) > 22:
        print("Error: Name is too long:", in_name)
        sys.exit()

    if in_name[:1] == "P":
        # print("Processing XP:", input_string[2:])
        pos_type_dict[in_name] = 'P'

    elif in_name[:1] == "J":
        # print("Processing XJ:", input_string[2:])
        pos_type_dict[in_name] = 'J'

    else:
        # Default action for other cases
        print("ERROR Unknown prefix in name:", in_name)
        sys.exit()


def generate_end_dats(name, tool, base, number, type):
    if type == 'P':
        pos_dat_code = f'''DECL LDAT LCPDAT{number}={{VEL 2.00000,ACC 100.000,APO_DIST 500.000,APO_FAC 50.0000,AXIS_VEL 100.000,AXIS_ACC 100.000,ORI_TYP #VAR,CIRC_TYP #BASE,JERK_FAC 50.0000,GEAR_JERK 100.000,EXAX_IGN 0,CB {{AUX_PT {{ORI #CONSIDER,E1 #CONSIDER,E2 #CONSIDER,E3 #CONSIDER,E4 #CONSIDER,E5 #CONSIDER,E6 #CONSIDER}},TARGET_PT {{ORI #INTERPOLATE,E1 #INTERPOLATE,E2 #INTERPOLATE,E3 #INTERPOLATE,E4 #INTERPOLATE,E5 #INTERPOLATE,E6 #INTERPOLATE}}}}}}
DECL FDAT F{name}={{TOOL_NO {tool},BASE_NO {base},IPO_FRAME #BASE,POINT2[] " "}}

'''
    if type == 'J':
        pos_dat_code = f'''DECL PDAT PPDAT{number}={{VEL 100.000,ACC 100.000,APO_DIST 500.000,APO_MODE #CDIS,GEAR_JERK 100.000,EXAX_IGN 0}}
DECL FDAT F{name}={{TOOL_NO {tool},BASE_NO {base},IPO_FRAME #BASE,POINT2[] " "}}
        
'''
    return pos_dat_code


def generate_dat(name, type):
    if type == 'P':
        in_dat = f'DECL GLOBAL POS X{name} = {{ X 0.0, Y 0.0, Z 0.0, A 0.0, B 0.0, C 0.0, S 0, T 0}}\n'
    if type == 'J':
        in_dat = f'DECL GLOBAL AXIS X{name}={{A1 0.0, A2 0.0, A3 0.0, A4 0.0, A5 0.0, A6 0.0}}\n'
    return in_dat


def dat_contsturct(in_dict):
    in_output = 'DEFDAT TEACHPROGRAM PUBLIC\n\n'

    if in_dict['nonfold'] is not None:  # if nonfold has content
        for pos in in_dict['nonfold']:
            in_output += generate_dat(pos['name'], pos_type_dict[pos['name']])

    # if there are actual folds
    if len([key for key in in_dict.keys() if isinstance(in_dict[key], dict) and key != 'nonfold']) != 0:
        for folds in in_dict:
            if folds != 'nonfold':  # go through folds
                in_output += f';FOLD {folds}\n\n'
                # if folds is just a list of pos dictionaries
                if isinstance(in_dict[folds], list):
                    for pos in folds:
                        in_output += generate_dat(pos['name'],
                                                  pos_type_dict[pos['name']])
                else:   # if folds has subfolds
                    for subfold in in_dict[folds]:
                        # if nonsubfold has content
                        if subfold == 'nonsubfold' and in_dict[folds]['nonsubfold'] is not None:
                            for pos in in_dict[folds]['nonsubfold']:
                                in_output += generate_dat(
                                    pos['name'], pos_type_dict[pos['name']])
                        if subfold != 'nonsubfold':
                            in_output += f';FOLD sub {subfold}\n\n'
                            for pos in in_dict[folds][subfold]:
                                in_output += generate_dat(
                                    pos['name'], pos_type_dict[pos['name']])
                            in_output += ';ENDFOLD sub\n\n'
                in_output += ';ENDFOLD\n\n'
    return in_output


def generate_posteach(name, tool, base, number, pos_type):

    if name[:1] == "X":  # if name starts with X, delete it
        name = name[1:]

    if pos_type == 'P':
        pos_teach_code = f''';FOLD LIN {name} Vel=2 m/s CPDAT{number} Tool[{tool}] Base[{base}] ;%{{PE}}
   ;FOLD Parameters ;%{{h}}
      ;Params IlfProvider=kukaroboter.basistech.inlineforms.movement.old; Kuka.IsGlobalPoint=False; Kuka.PointName={name}; Kuka.BlendingEnabled=False; Kuka.MoveDataName=CPDAT{number}; Kuka.VelocityPath=2; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=LIN
   ;ENDFOLD
   $BWDSTART = FALSE
   LDAT_ACT = LCPDAT{number}
   FDAT_ACT = F{name}
   BAS(#CP_PARAMS, 2.0)
   SET_CD_PARAMS (0)
   LIN X{name}
;ENDFOLD
HALT

'''
    if pos_type == 'J':
        pos_teach_code = f''';FOLD PTP {name} Vel=100 % PDAT{number} Tool[{tool}] Base[{base}] ;%{{PE}}
   ;FOLD Parameters ;%{{h}}
      ;Params IlfProvider=kukaroboter.basistech.inlineforms.movement.old; Kuka.IsGlobalPoint=False; Kuka.PointName={name}; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=PDAT{number}; Kuka.VelocityPtp=100; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=PTP
   ;ENDFOLD
   $BWDSTART = FALSE
   PDAT_ACT = PPDAT{number}
   FDAT_ACT = F{name}
   BAS(#PTP_PARAMS, 100.0)
   SET_CD_PARAMS (0)
   PTP X{name}
;ENDFOLD
HALT

'''

    return pos_teach_code


def create_pos_structure(in_dict):
    in_output = 'DEF TeachProgram ( )\n\n'

    if in_dict['nonfold'] is not None:  # if nonfold has content
        for pos in in_dict['nonfold']:
            in_output += generate_posteach(pos['name'],
                                           pos['tool'], pos['base'], pos['number'], pos_type_dict[pos['name']])

    # if there are actual folds
    if len([key for key in in_dict.keys() if isinstance(in_dict[key], dict) and key != 'nonfold']) != 0:
        for folds in in_dict:
            if folds != 'nonfold':  # go through folds
                in_output += f';FOLD {folds}\n\n'
                # if folds is just a list of pos dictionaries
                if isinstance(in_dict[folds], list):
                    for pos in folds:
                        in_output += generate_posteach(
                            pos['name'], pos['tool'], pos['base'], pos['number'], pos_type_dict[pos['name']])
                else:   # if folds has subfolds
                    for subfold in in_dict[folds]:
                        # if nonsubfold has content
                        if subfold == 'nonsubfold' and in_dict[folds]['nonsubfold'] is not None:
                            for pos in in_dict[folds]['nonsubfold']:
                                in_output += generate_posteach(
                                    pos['name'], pos['tool'], pos['base'], pos['number'], pos_type_dict[pos['name']])
                        if subfold != 'nonsubfold':
                            in_output += f';FOLD sub {subfold}\n\n'
                            for pos in in_dict[folds][subfold]:
                                in_output += generate_posteach(
                                    pos['name'], pos['tool'], pos['base'], pos['number'], pos_type_dict[pos['name']])
                            in_output += ';ENDFOLD sub\n\n'
                in_output += ';ENDFOLD\n\n'
    return in_output


def loop_in_dict(in_dict):
    result = []
    for key, value in in_dict.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    for item in sub_value:
                        if isinstance(item, dict):
                            if 'name' in item:
                                result.append(
                                    [item['name'], item['tool'], item['base'], item['number']])
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    if 'name' in item:
                        result.append(
                            [item['name'], item['tool'], item['base'], item['number']])
    return result


def detect_csv_separator(in_csvdata):
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(in_csvdata)
    file.seek(0)  # Reset file pointer to beginning
    return dialect.delimiter


#####################################################
#                       MAIN                        #
print('''*********************************
| Welcome to TeachPos Generator |
*********************************
from your excel, copy-paste your positions in a text file and save it as pos.csv in the same fold as this script
COLUMN ORDER: Name, Tool, Base (do not include header!)
For more information visit: https://github.com/zserub/TeachPos-Generator?tab=readme-ov-file#kuka-position-teaching-program-generator-from-csv-file

''')
# input("Press Enter to start the script")

# Read CSV file
data = []
try:
    with open(csv_file_path, mode='r') as file:
        # Detect the CSV separator
        separator = detect_csv_separator(file.read(1024))
        if separator:
            print(f"The CSV separator in {csv_file_path} is: {separator}")
        else:
            print("Failed to detect CSV separator.")

        # Create a CSV reader object with the detected delimiter
        reader = csv.reader(file, delimiter=separator)
        # Iterate over each row in the CSV file
        for row in reader:
            # Append each row to the data list
            data.append(row)
except FileNotFoundError:
    print(f"Error: The file '{csv_file_path}' was not found.")
    sys.exit()
except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
    sys.exit()

# Process CSV data
header_map = {}
fold_hierarchy = FoldHierarchy()
try:
    fold_count = process_header(data[0])
    process_csv(data, fold_count)
except Exception as errormessage:
    print(errormessage)
    sys.exit()

pos_type_dict = {}
for key, value in parsed_dict.items():
    if isinstance(value, dict):
        for sub_key, sub_value in value.items():
            if isinstance(sub_value, list):
                for item in sub_value:
                    if isinstance(item, dict):
                        if 'name' in item:
                            recognise_type(item['name'])
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                if 'name' in item:
                    recognise_type(item['name'])

out_pos = create_pos_structure(parsed_dict)
out_pos += '\nEND'
out_dat = dat_contsturct(parsed_dict)

out_dat += '\n\n;FOLD DATs\n'
poslist = loop_in_dict(parsed_dict)
for pos in poslist:
    out_dat += generate_end_dats(pos[0], pos[1],
                                 pos[2], pos[3], pos_type_dict[pos[0]])
out_dat += ';ENDFOLD\nENDDAT'

filename1 = 'TeachProgram.src'
with open(filename1, 'w') as file:
    file.write(out_pos)

filename2 = 'TeachProgram.dat'
with open(filename2, 'w') as file:
    file.write(out_dat)


print(f'The code has been written to {filename1} and {filename2}')
