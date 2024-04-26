import sys
import csv
import re

csv_file_path = './pos.csv'


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
            # print(f"Fold '{fold_name}' already exists.")
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


def unX(name):
    if name.startswith("X") or name.startswith("x"):  # if name starts with X, delete it
        name = name[1:]
    return name


def parse_header(headers):
    # Check if csv structure is correct
    expected_headers = {'name', 'tool', 'base'}
    missing_headers = expected_headers - {h.lower() for h in headers}
    if missing_headers:
        raise Exception(
            f'Error: Invalid CSV structure; missing columns: {", ".join(missing_headers)}')

    fold_headers = [h for h in headers if h.lower().startswith('fold')]
    fold_count = len(fold_headers)
    if fold_count > 0:
        print(f"Number of folds: {fold_count}")
    else:
        raise Exception(
            "Error: Invalid CSV structure; No fold column found.\nIf you don't want to create any fold, make a fold column as `root`")

    header_map = {}
    numbering = 1
    for index, header in enumerate(headers):
        if fold_count > 0:
            if re.match('FOLD', header, re.IGNORECASE):
                key = 'fold' + str(numbering)
                header_map[key] = index
                numbering += 1
            else:
                header_map[header.lower()] = index
    return fold_count, header_map


def parse_data(in_data, in_fold_count, start_number, header_map):
    fold_hierarchy = FoldHierarchy()
    number = start_number-1

    for row in in_data[1:]:
        name = unX(row[header_map['name']])
        tool = int(row[header_map['tool']])
        base = int(row[header_map['base']])
        number += 1

        position = Position(name, tool, base, number)

        fold_names = [
            row[header_map[f'fold{i+1}']] for i in range(in_fold_count)]

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

    return fold_hierarchy


def recognise_type(in_name):
    out_type = ''

    if len(in_name) > 22:
        print("Error: Name is too long:", in_name)
        sys.exit(1)

    if in_name.startswith("P") or in_name.startswith("p"):
        out_type = 'P'

    elif in_name.startswith("J") or in_name.startswith("j"):
        out_type = 'J'

    else:
        # Default action for other cases
        print("ERROR Unknown prefix in name:", in_name)
        sys.exit(1)

    return out_type


def generate_dat_code(fold):
    out_dat = ''

    # Print the current fold
    if fold.name != 'root':
        out_dat += f';FOLD {fold.name}\n'

    for position in fold.positions:
        name = position.name
        type = recognise_type(name)

        if type == 'P':
            out_dat += f'DECL GLOBAL POS X{name} = {{ X 0.0, Y 0.0, Z 0.0, A 0.0, B 0.0, C 0.0, S 0, T 0}}\n'
        if type == 'J':
            out_dat += f'DECL GLOBAL AXIS X{name}={{A1 0.0, A2 0.0, A3 0.0, A4 0.0, A5 0.0, A6 0.0}}\n'

    # Recursively print the subfolds
    for subfold in fold.subfolds.values():
        out_dat += generate_dat_code(subfold)

    # Add the ENDFOLD string
    if fold.name != 'root':
        out_dat += f';ENDFOLD {fold.name}\n'

    return out_dat


def generate_end_dats(fold):

    pos_dat_code = ''

    for position in fold.positions:
        number = position.number
        name = position.name
        tool = position.tool
        base = position.base
        type = recognise_type(name)

        if type == 'P':
            pos_dat_code += f'''DECL LDAT LCPDAT{number}={{VEL 2.00000,ACC 100.000,APO_DIST 500.000,APO_FAC 50.0000,AXIS_VEL 100.000,AXIS_ACC 100.000,ORI_TYP #VAR,CIRC_TYP #BASE,JERK_FAC 50.0000,GEAR_JERK 100.000,EXAX_IGN 0,CB {{AUX_PT {{ORI #CONSIDER,E1 #CONSIDER,E2 #CONSIDER,E3 #CONSIDER,E4 #CONSIDER,E5 #CONSIDER,E6 #CONSIDER}},TARGET_PT {{ORI #INTERPOLATE,E1 #INTERPOLATE,E2 #INTERPOLATE,E3 #INTERPOLATE,E4 #INTERPOLATE,E5 #INTERPOLATE,E6 #INTERPOLATE}}}}}}
DECL FDAT F{name}={{TOOL_NO {tool},BASE_NO {base},IPO_FRAME #BASE,POINT2[] " "}}

'''
        if type == 'J':
            pos_dat_code += f'''DECL PDAT PPDAT{number}={{VEL 100.000,ACC 100.000,APO_DIST 500.000,APO_MODE #CDIS,GEAR_JERK 100.000,EXAX_IGN 0}}
DECL FDAT F{name}={{TOOL_NO {tool},BASE_NO {base},IPO_FRAME #BASE,POINT2[] " "}}

'''

    # Recursively print the subfolds
    for subfold in fold.subfolds.values():
        pos_dat_code += generate_end_dats(subfold)

    return pos_dat_code


def generate_src_code(name, tool, base, number, pos_type):

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


def src_string_to_file(fold_hierarchy):
    out_pos = 'DEF TeachProgram ( )\n\n'
    out_pos = create_fold_struct_for_src(fold_hierarchy.root_fold)
    out_pos += '\nEND'

    # Write files
    with open('TeachProgram.src', 'w') as file:
        file.write(out_pos)


def dat_string_to_file(fold_hierarchy):
    out_dat = 'DEFDAT TEACHPROGRAM PUBLIC\n\n'
    out_dat += generate_dat_code(fold_hierarchy.root_fold)
    out_dat += '\n\n;FOLD DATs\n'
    out_dat += generate_end_dats(fold_hierarchy.root_fold)
    out_dat += ';ENDFOLD\nENDDAT'

    with open('TeachProgram.dat', 'w') as file:
        file.write(out_dat)


def create_fold_struct_for_src(fold):
    output_string = ''

    # Print the current fold
    if fold.name != 'root':
        output_string += f';FOLD {fold.name}\n'

    for position in fold.positions:
        output_string += generate_src_code(position.name, position.tool,
                                           position.base, position.number, recognise_type(position.name))

    # Recursively print the subfolds
    for subfold in fold.subfolds.values():
        output_string += create_fold_struct_for_src(subfold)

    # Add the ENDFOLD string
    if fold.name != 'root':
        output_string += f';ENDFOLD {fold.name}\n'

    return output_string


def detect_csv_separator(in_csvdata):
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(in_csvdata)
    return dialect.delimiter


def read_csv(csv_file_path):
    data = []
    try:
        with open(csv_file_path, mode='r') as file:
            # Detect the CSV separator
            separator = detect_csv_separator(file.read(1024))
            file.seek(0)  # Reset file pointer to beginning
            if separator:
                print(f"The CSV separator in {csv_file_path} is: {separator}")
            else:
                print("Failed to detect CSV separator.")

            # Create a CSV reader object with the detected delimiter
            reader = csv.reader(file, delimiter=separator)
            #  Iterate over each row in the CSV file
            for row in reader:
                # Append each row to the data list after cleaning whitespaces
                data.append([item.strip() for item in row])

    except FileNotFoundError:
        print(f"Error: The file '{csv_file_path}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

    return data


def get_valid_start_number():
    while True:
        try:
            start_number = int(input(
                "Type in the first number and press enter to start the generation...\nStart number: "))
            if start_number > 0:
                return start_number
            else:
                print("\nERROR: Start number must be greater than 0!")
        except ValueError:
            print("\nERROR: Invalid input. Please enter a number.")


def main():
    print('''*********************************
    | Welcome to TeachPos Generator |
    *********************************
    Create your pos.csv in the same folder as this script

    For more information visit: https://github.com/zserub/TeachPos-Generator

    ''')

    start_number = get_valid_start_number()
    data = read_csv(csv_file_path)

    # Process CSV data
    try:
        fold_count, header_map = parse_header(data[0])
        fold_hierarchy = parse_data(
            data, fold_count, start_number, header_map)
    except Exception as errormessage:
        print(errormessage)
        sys.exit(1)

    src_string_to_file(fold_hierarchy)
    dat_string_to_file(fold_hierarchy)

    print(f'The code has been written to TeachProgram.src and TeachProgram.dat.')


if __name__ == "__main__":
    main()
