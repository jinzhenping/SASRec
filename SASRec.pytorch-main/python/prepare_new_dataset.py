"""
새로운 데이터셋을 SASRec 형식으로 변환하는 스크립트

사용법:
    python prepare_new_dataset.py --input your_data.csv --output data/my_dataset.txt

입력 형식 예시 (CSV):
    user_id,item_id,timestamp
    1,100,2023-01-01 10:00:00
    1,200,2023-01-01 11:00:00
    ...

또는 다른 형식에 맞게 수정하여 사용하세요.
"""

import argparse
import pandas as pd
from collections import defaultdict

def convert_to_sasrec_format(input_file, output_file, user_col='user_id', item_col='item_id', 
                             time_col='timestamp', delimiter=','):
    """
    데이터를 SASRec 형식으로 변환
    
    Args:
        input_file: 입력 파일 경로
        output_file: 출력 파일 경로 (data/ 폴더에 저장)
        user_col: 사용자 ID 컬럼명
        item_col: 아이템 ID 컬럼명
        time_col: 시간 컬럼명 (정렬용)
        delimiter: 구분자 (CSV면 ',', TSV면 '\t')
    """
    # 데이터 읽기
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    elif input_file.endswith('.tsv'):
        df = pd.read_csv(input_file, delimiter='\t')
    else:
        # 일반 텍스트 파일 처리
        df = pd.read_csv(input_file, delimiter=delimiter)
    
    # 시간 순서로 정렬
    if time_col in df.columns:
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.sort_values([user_col, time_col])
    
    # 사용자별로 그룹화하여 시퀀스 생성
    user_sequences = defaultdict(list)
    for _, row in df.iterrows():
        user_id = row[user_col]
        item_id = row[item_col]
        user_sequences[user_id].append(item_id)
    
    # 사용자 ID와 아이템 ID를 1부터 시작하는 연속된 정수로 매핑
    unique_users = sorted(user_sequences.keys())
    unique_items = set()
    for items in user_sequences.values():
        unique_items.update(items)
    unique_items = sorted(unique_items)
    
    user_map = {old_id: new_id for new_id, old_id in enumerate(unique_users, start=1)}
    item_map = {old_id: new_id for new_id, old_id in enumerate(unique_items, start=1)}
    
    # 변환된 데이터 쓰기
    with open(output_file, 'w') as f:
        for old_user_id in unique_users:
            new_user_id = user_map[old_user_id]
            for old_item_id in user_sequences[old_user_id]:
                new_item_id = item_map[old_item_id]
                f.write(f"{new_user_id} {new_item_id}\n")
    
    print(f"변환 완료!")
    print(f"  - 총 사용자 수: {len(unique_users)}")
    print(f"  - 총 아이템 수: {len(unique_items)}")
    print(f"  - 총 상호작용 수: {len(df)}")
    print(f"  - 출력 파일: {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='데이터셋을 SASRec 형식으로 변환')
    parser.add_argument('--input', required=True, help='입력 파일 경로')
    parser.add_argument('--output', required=True, help='출력 파일 경로 (예: data/my_dataset.txt)')
    parser.add_argument('--user_col', default='user_id', help='사용자 ID 컬럼명')
    parser.add_argument('--item_col', default='item_id', help='아이템 ID 컬럼명')
    parser.add_argument('--time_col', default='timestamp', help='시간 컬럼명')
    parser.add_argument('--delimiter', default=',', help='구분자 (CSV: ",", TSV: "\\t")')
    
    args = parser.parse_args()
    
    convert_to_sasrec_format(
        args.input, 
        args.output,
        args.user_col,
        args.item_col,
        args.time_col,
        args.delimiter
    )

