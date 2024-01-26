import sys
import pandas as pd
import csv

def recognise_type(input_string, tool, base):
    pos_dat_code=''
    
    if input_string[:1] == "X":
        input_string = input_string[1:]

    
    if input_string[:1] == "P":
        # print("Processing XP:", input_string[2:])
        pos_dat_code=generate_XP(input_string, tool, base)
        
    elif input_string[:1] == "J":
        # print("Processing XJ:", input_string[2:])
        pos_dat_code=generate_XJ(input_string, tool, base)
        
    else:
        # Default action for other cases
        print("ERROR Unknown prefix:", input_string)
        sys.exit()
    
    file.write(pos_dat_code)
        
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
    
    if name[:1] == "X":     #if name starts with X, delete it
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
    file.write(pos_teach_code)
            
            
def detect_csv_separator(csv_file_path):
    with open(csv_file_path, 'r', newline='') as file:
        try:
            dialect = csv.Sniffer().sniff(file.read(1024))
            return dialect.delimiter
        except csv.Error as e:
            print(f"Error detecting CSV separator: {e}")
            return None
            
            
            
#MAIN
print('''*********************************
| Welcome to TeachPos Generator |
*********************************
from your excel, copy-paste your positions in a text file and save it as pos.csv in the same folder as this script
COLUMN ORDER: Name, Tool, Base (do not include header!)
''')
# Wait for user input
input("Press Enter to start the script")

csv_file_path = './pos.csv'
df = None

csv_file_path = './pos.csv'
separator = detect_csv_separator(csv_file_path)

if separator:
    print(f"The CSV separator in {csv_file_path} is: {separator}")
else:
    print("Unable to detect CSV separator.")


try:
    df = pd.read_csv(csv_file_path, sep=separator, header=None, names=['Name', 'Tool', 'Base'])
    print(f"CSV file successfully loaded")

except FileNotFoundError:
    print(f"Error: The file '{csv_file_path}' was not found.")
    sys.exit()
except pd.errors.EmptyDataError:
    print(f"Error: The file '{csv_file_path}' is empty.")
    sys.exit()
except pd.errors.ParserError:
    print(f"Error: Unable to parse the CSV file '{csv_file_path}'. Please check the file format.")
    sys.exit()
except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
    sys.exit()

filename2 = f'generated_pos.dat'
with open(filename2, 'w') as file:    
    # Iterate over the rows of the DataFrame and call generated_pos_dat
    for index, row in df.iterrows():
        recognise_type(row['Name'], row['Tool'], row['Base'])        
        
filename1 = f'generated_posteach.src'
with open(filename1, 'w') as file:    
    # Iterate over the rows of the DataFrame and call generate_posteach
    for index, row in df.iterrows():
        generate_posteach(row['Name'], row['Tool'], row['Base'])

print(f'The code has been written to {filename1} and {filename2}')
