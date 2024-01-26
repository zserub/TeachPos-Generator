import sys
import csv
import re

csv_file_path = './pos.csv'
output = ''
# nofold=False


def parse_csv(in_data):
    nonfold = []
    data_dictionary = {'nonfold': nonfold}
    fold_key = None
    sub_key = None

    for line in in_data:
        if re.match(r'^FOLD', line, re.IGNORECASE):  # it's a fold
            # cut down the ;FOLD and place the fold name in folds dictionary
            fold_key = line[len('FOLD '):]
            fold_key = fold_key.strip()

            if fold_key not in data_dictionary:
                data_dictionary[fold_key] = {}
            else:
                print(f"Error: Duplicate fold name '{fold_key}'")
                sys.exit()

            sub_key=None

        elif re.match(r'^SUBFOLD', line, re.IGNORECASE):
            # cut down the ;SUBFOLD and place the fold name in folds dictionary
            sub_key = line[len('SUBFOLD '):]
            sub_key = sub_key.strip()

            if sub_key not in data_dictionary[fold_key]:
                data_dictionary[fold_key][sub_key] = []
            else:
                print(f"Error: Duplicate subfold name '{sub_key}'")
                sys.exit()

        elif line:
            # break line into data parts
            parts = line.split(separator)
            name = parts[0]
            try:
                values = list(map(int, parts[1:]))
            except ValueError:
                print(f"Error: Non-integer value in line '{line}'")
                sys.exit()

            # add data into the dictionary
            if fold_key is not None:
                if sub_key is None:
                    if 'nonsubfold' not in data_dictionary[fold_key]:
                        data_dictionary[fold_key]['nonsubfold'] = []
                    data_dictionary[fold_key]['nonsubfold'].append({'name': name, 'tool': values[0], 'base': values[1]})
                else:
                    data_dictionary[fold_key][sub_key].append(
                        {'name': name, 'tool': values[0], 'base': values[1]})

            else:
                data_dictionary[nonfold].append(
                        {'name': name, 'tool': values[0], 'base': values[1]})
    return data_dictionary


def filterCSV(lines):
    in_data = []
    for line in lines:
        if not re.match(r'^fold|subfold', line, re.IGNORECASE):
            in_data.append(line)
    return in_data


def recognise_type(input_string):
    pos_dat_code = ''

    if input_string[:1] == "X":
        input_string = input_string[1:]

    if input_string[:1] == "P":
        # print("Processing XP:", input_string[2:])
        pos_dat_code = generate_XP(input_string)

    elif input_string[:1] == "J":
        # print("Processing XJ:", input_string[2:])
        pos_dat_code = generate_XJ(input_string)

    else:
        # Default action for other cases
        print("ERROR Unknown prefix in name:", input_string)
        sys.exit()

    return pos_dat_code


def generate_XP(name, tool, base):
    pos_dat_code = f'''DECL PDAT PPDAT_{name} = {{APO_MODE #CDIS, APO_DIST 500, VEL 100, ACC 100, GEAR_JERK 100.0, EXAX_IGN 0}}
DECL FDAT F{name} = {{BASE_NO {base}, TOOL_NO {tool}, IPO_FRAME #BASE, POINT2[] " "}}
DECL GLOBAL POS X{name} = {{ X 0.0, Y 0.0, Z 0.0, A 0.0, B 0.0, C 0.0, S 0, T 0}}

'''
    return pos_dat_code


def generate_XJ(name, tool, base):
    pos_dat_code = f'''DECL PDAT PPDAT_{name}={{VEL 100.000, ACC 100.000, APO_DIST 500.000, APO_MODE #CDIS, GEAR_JERK 100.000, EXAX_IGN 0}}
DECL FDAT F{name} = {{BASE_NO {base}, TOOL_NO {tool}, IPO_FRAME #BASE, POINT2[] " "}}
DECL GLOBAL AXIS X{name}={{A1 0.0, A2 0.0, A3 0.0, A4 0.0, A5 0.0, A6 0.0}}

'''
    return pos_dat_code


def generate_posteach(name, tool, base):

    if name[:1] == "X":  # if name starts with X, delete it
        name = name[1:]

    pos_teach_code = f''';FOLD PTP {name} Vel=100 % PDAT_{name} Tool[{tool}] Base[{base}] ;%{{PE}}
   ;FOLD Parameters ;%{{h}}
      ;Params IlfProvider=kukaroboter.basistech.inlineforms.movement.old; Kuka.IsGlobalPoint=False; Kuka.PointName={name}; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=PDAT_{name}; Kuka.VelocityPtp=100; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=PTP
   ;ENDFOLD
   $BWDSTART = FALSE
   PDAT_ACT = PPDAT_{name}
   FDAT_ACT = F{name}
   BAS(#PTP_PARAMS, 100.0)
   SET_CD_PARAMS (0)
   PTP X{name}
;ENDFOLD
HALT

'''
    return pos_teach_code


def create_structure(in_dict):
    in_output = ''
    
    if in_dict['nonfold'] is not None:  # if nonfold has content
        for pos in in_dict['nonfold']:
            in_output += generate_posteach(pos['name'], pos['tool'], pos['base'])
            
    # if there are actual folds
    if len([key for key in in_dict.keys() if isinstance(in_dict[key], dict) and key != 'nonfold']) != 0: 
        for folds in in_dict:
            if folds != 'nonfold':  # go through folds
                in_output += f';FOLD {folds}\n\n'
                if isinstance(in_dict[folds], list):  # if folds is just a list of pos dictionaries
                    for pos in folds:
                        in_output += generate_posteach(pos['name'], pos['tool'], pos['base'])
                else:   # if folds has subfolds
                    for subfold in in_dict[folds]:
                        if subfold == 'nonsubfold' and in_dict[folds]['nonsubfold'] is not None:  # if nonsubfold has content
                            for pos in in_dict[folds]['nonsubfold']:
                                in_output += generate_posteach(pos['name'], pos['tool'], pos['base'])
                        if subfold != 'nonsubfold':
                            in_output += f';FOLD sub {subfold}\n\n'
                            for pos in in_dict[folds][subfold]:
                                in_output += generate_posteach(pos['name'], pos['tool'], pos['base'])
                            in_output += ';ENDFOLD sub\n\n'
                in_output += ';ENDFOLD\n\n'
    return in_output

def detect_csv_separator(in_csvdata):
    csv_content = '\n'.join(in_csvdata)
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(csv_content)
        return dialect.delimiter
    except csv.Error as e:
        print(f"Error detecting CSV separator: {e}")
        sys.exit()


#####################################################
#                       MAIN                        #
print('''*********************************
| Welcome to TeachPos Generator |
*********************************
from your excel, copy-paste your positions in a text file and save it as pos.csv in the same folder as this script
COLUMN ORDER: Name, Tool, Base (do not include header!)
For folding: create rows with "FOLD Name"

''')
input("Press Enter to start the script")

# Try to open the CSV file
try:
    with open(csv_file_path, 'r') as file:
        lines = file.readlines()
except FileNotFoundError:
    print(f"Error: The file '{csv_file_path}' was not found.")
    sys.exit()
except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
    sys.exit()


cleancsv = filterCSV(lines)
# Detect the CSV separator
separator = detect_csv_separator(cleancsv)
if separator:
    print(f"The CSV separator in {csv_file_path} is: {separator}")
else:
    print("Unable to detect CSV separator.")

parsed_data = parse_csv(lines)

output = create_structure(parsed_data)

# first_fold_key = next(iter(parsed_data), None)
# for foldname in parsed_data:
# print(foldname, ':{')
# for fold in parsed_data[foldname]:
#     print(f"\t{fold['name']}, {fold['tool']}, {fold['base']}")
# print('}')
# for fold in parsed_data:
#     output_dat = recognise_type(fold['name'])

# filename2 = 'generated_pos.dat'
# with open(filename2, 'w') as file:

filename1 = 'generated_posteach.src'
with open(filename1, 'w') as file:
    file.write(output)

print(f'The code has been written to {filename1}')  # and {filename2}')
