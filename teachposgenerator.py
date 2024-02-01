import sys
import csv
import re

csv_file_path = './pos.csv'
out_pos = ''
out_dat = ''


def parse_csv(in_data):
    # nonfold = ''
    data_dictionary = {'nonfold': []}
    fold_key = None
    sub_key = None
    number = 0

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

            sub_key = None

        elif re.match(r'^SUBFOLD', line, re.IGNORECASE):
            # cut down the ;SUBFOLD and place the fold name in folds dictionary
            sub_key = line[len('SUBFOLD '):]
            sub_key = sub_key.strip()

            if fold_key is None:
                print(f"Error: Subfold without fold '{sub_key}'")
                sys.exit()
            if sub_key not in data_dictionary[fold_key]:
                data_dictionary[fold_key][sub_key] = []
            else:
                print(f"Error: Duplicate subfold name '{sub_key}'")
                sys.exit()

        elif line:
            # line is position data, break it into data parts
            number += 1
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
                    data_dictionary[fold_key]['nonsubfold'].append(
                        {'name': name, 'tool': values[0], 'base': values[1], 'number': number})
                else:
                    data_dictionary[fold_key][sub_key].append(
                        {'name': name, 'tool': values[0], 'base': values[1], 'number': number})

            else:
                data_dictionary['nonfold'].append(
                    {'name': name, 'tool': values[0], 'base': values[1], 'number': number})
    return data_dictionary


def filterCSV(lines):
    in_data = ''
    for line in lines:
        if not re.match(r'^fold|subfold', line, re.IGNORECASE):
            in_data += line
    return in_data


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
        pos_dat_code = f'''DECL PDAT PPDAT{number}={{VEL 100.000,ACC 100.000,APO_DIST 500.000,APO_MODE #CDIS,GEAR_JERK 100.000,EXAX_IGN 0}}
DECL FDAT F{name}={{TOOL_NO {tool},BASE_NO {base},IPO_FRAME #BASE,POINT2[] " "}}

'''
    if type == 'J':
        pos_dat_code = f'''DECL LDAT LCPDAT{number}={{VEL 2.00000,ACC 100.000,APO_DIST 500.000,APO_FAC 50.0000,AXIS_VEL 100.000,AXIS_ACC 100.000,ORI_TYP #VAR,CIRC_TYP #BASE,JERK_FAC 50.0000,GEAR_JERK 100.000,EXAX_IGN 0,CB {{AUX_PT {{ORI #CONSIDER,E1 #CONSIDER,E2 #CONSIDER,E3 #CONSIDER,E4 #CONSIDER,E5 #CONSIDER,E6 #CONSIDER}},TARGET_PT {{ORI #INTERPOLATE,E1 #INTERPOLATE,E2 #INTERPOLATE,E3 #INTERPOLATE,E4 #INTERPOLATE,E5 #INTERPOLATE,E6 #INTERPOLATE}}}}}}
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
    in_output = 'DEFDAT  TEACHPROGRAM PUBLIC\n\n'

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
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(in_csvdata)
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
For more information visit: https://github.com/zserub/TeachPos-Generator?tab=readme-ov-file#kuka-position-teaching-program-generator-from-csv-file

''')
# input("Press Enter to start the script")

# Try to open the CSV file
try:
    with open(csv_file_path, 'r') as file:
        input_data = file.readlines()
except FileNotFoundError:
    print(f"Error: The file '{csv_file_path}' was not found.")
    sys.exit()
except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
    sys.exit()


cleancsv = filterCSV(input_data)
# Detect the CSV separator
separator = detect_csv_separator(cleancsv)
if separator:
    print(f"The CSV separator in {csv_file_path} is: {separator}")
else:
    print("Unable to detect CSV separator.")

parsed_dict = parse_csv(input_data)

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

filename1 = 'generated_posteach.src'
with open(filename1, 'w') as file:
    file.write(out_pos)

filename2 = 'generated_pos.dat'
with open(filename2, 'w') as file:
    file.write(out_dat)


print(f'The code has been written to {filename1} and {filename2}')
