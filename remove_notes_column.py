import pandas as pd

def remove_notes_column(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Tìm tên cột notes không phân biệt hoa thường
    notes_col = None
    for col in df.columns:
        if col.strip().lower() == 'notes':
            notes_col = col
            break
    
    if notes_col:
        # Xóa cột notes
        df = df.drop(notes_col, axis=1)
        df.to_csv(output_file, index=False)
        print(f"Đã xóa cột '{notes_col}'. File mới lưu là: {output_file}")
    else:
        print("Không tìm thấy cột 'notes' trong file.")

if __name__ == "__main__":
    # Use full path for input file
    file_name = r"d:\college\New folder\NHA408E _ Dictionary ngành và mã cp - Ngành (1).csv"
    input_file = file_name
    output_file = file_name
    
    remove_notes_column(input_file, output_file) 