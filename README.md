# KUKA position teaching program generator from csv file

## Requirements

- [Python](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)
- (Excel)

## Usage

Start the script with `START_script.bat`

If you don't have python it will warn you and offer a download link, remind you to add it to your PATH and try again.

If python is installed run the `START_script.bat` again.

Current version can handle 1 layer subfolding in the [csv file (click to see example)](https://github.com/zserub/TeachPos-Generator/blob/main/pos.csv)

### CSV creating rules:
- add position data in the following order: Name, Tool, Base
- Don't include header
- Any separator works
- For folding: Write `FOLD <name>` before the positions you want to put into that folder. It will fold everything till the next FOLD line. Same rules applied for subfolding but use `SUBFOLD <name>`
- Use SUBFOLD only in a FOLD
- You don't need to use folds, but if you do, each position must be in a folder.

You are allowed to
- add positions with or without folds and subfold
- with or without X in position names
  
> Position names cannot be longer then 23 characters