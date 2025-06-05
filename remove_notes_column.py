import pandas as pd

def remove_notes_column(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Tìm tên cột notes không phân biệt hoa thường
    notes_col = None
    for col in df.columns:
        if col.strip().lower() == 'Keywords'.strip().lower():
            notes_col = col
            break
    
    if notes_col:
        # Xóa cột notes
        df = df.drop(notes_col, axis=1)
        df.to_csv(output_file, index=False)
        print(f"Đã xóa cột '{notes_col}'. File mới lưu là: {output_file}")
    else:
        print(f"Không tìm thấy cột '{notes_col}' trong file.")

if __name__ == "__main__":
    # Use full path for input file
    file_name = r"d:\college\New folder\dictionary_sectors.csv"
    input_file = file_name
    output_file = file_name
    
    remove_notes_column(input_file, output_file) 