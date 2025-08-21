import os
FOLDER_PATH = './sample_files/educatie'

for file in os.listdir(FOLDER_PATH):
  with open(os.path.join(FOLDER_PATH, file), 'r') as f:
    content = f.read()
    if 'nr.' in content or 'Nr.' in content:
      print(f"Fisierul {file} contine legi")