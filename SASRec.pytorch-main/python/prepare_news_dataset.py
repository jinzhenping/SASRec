"""
뉴스 히스토리 데이터를 SASRec 형식으로 변환하는 스크립트

입력 형식:
    user_id\titem1 item2 item3 ...
    예: 1001\tN39011 N112324 N78884 N111503

출력 형식:
    user_id item_id
    예: 1 1
        1 2
        1 3
        ...

사용법:
    python prepare_news_dataset.py --input your_data.tsv --output data/my_dataset.txt
"""

import argparse
from collections import defaultdict, OrderedDict

def convert_news_to_sasrec(input_file, output_file, keep_original_user_ids=False, remove_n_prefix=False):
    """
    뉴스 히스토리 데이터를 SASRec 형식으로 변환
    
    Args:
        input_file: 입력 파일 경로 (TSV 형식)
        output_file: 출력 파일 경로 (data/ 폴더에 저장)
        keep_original_user_ids: True면 원본 사용자 ID 유지, False면 1부터 시작하는 새 ID로 매핑
        remove_n_prefix: True면 아이템 ID에서 "N" 접두사 제거 (예: N39011 → 39011)
    """
    print(f"입력 파일 읽는 중: {input_file}")
    
    # 사용자별 아이템 시퀀스 저장
    user_sequences = defaultdict(list)
    all_items = set()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:  # 빈 라인 건너뛰기
                continue
            
            # 탭으로 분리
            parts = line.split('\t')
            if len(parts) < 2:
                print(f"경고: 라인 {line_num}에서 형식 오류 (탭으로 구분되지 않음): {line[:50]}...")
                continue
            
            user_id_str = parts[0].strip()
            items_str = parts[1].strip()
            
            # 사용자 ID 확인
            try:
                user_id = int(user_id_str)
            except ValueError:
                print(f"경고: 라인 {line_num}에서 사용자 ID를 정수로 변환할 수 없음: {user_id_str}")
                continue
            
            # 아이템 리스트 파싱 (공백으로 구분)
            items = items_str.split()
            if not items:
                print(f"경고: 라인 {line_num}에서 아이템이 없음")
                continue
            
            # 아이템 저장 (중복 제거하지 않고 순서 유지)
            for item in items:
                item = item.strip()
                if item:  # 빈 문자열이 아닌 경우만
                    # "N" 접두사 제거 옵션
                    if remove_n_prefix and item.startswith('N'):
                        # N39011 → 39011
                        try:
                            item_id = int(item[1:])  # 첫 글자 제거 후 정수 변환
                            processed_item = str(item_id)
                        except ValueError:
                            # 숫자로 변환 실패 시 원본 유지
                            processed_item = item
                    else:
                        processed_item = item
                    
                    user_sequences[user_id].append(processed_item)
                    all_items.add(processed_item)
    
    print(f"  - 총 사용자 수: {len(user_sequences)}")
    print(f"  - 총 고유 아이템 수: {len(all_items)}")
    
    # 아이템 ID 처리
    unique_items = sorted(all_items)  # 정렬하여 일관된 매핑 보장
    
    if remove_n_prefix:
        # "N" 접두사가 제거된 경우, 숫자 ID를 그대로 사용
        # 단, 1부터 시작하지 않을 수 있으므로 확인 필요
        item_map = {}
        numeric_items = []
        for item in unique_items:
            try:
                item_id = int(item)
                item_map[item] = item_id  # 원본 숫자 ID 그대로 사용
                numeric_items.append(item_id)
            except ValueError:
                # 숫자가 아닌 경우 기존 방식으로 매핑
                item_map[item] = len(item_map) + 1
        
        print(f"  - 아이템 ID에서 'N' 접두사 제거됨")
        if numeric_items:
            print(f"  - 아이템 ID 범위: {min(numeric_items)} ~ {max(numeric_items)}")
    else:
        # 아이템 ID를 1부터 시작하는 연속된 정수로 매핑
        item_map = {item: idx + 1 for idx, item in enumerate(unique_items)}
    
    # 사용자 ID 처리
    unique_users = sorted(user_sequences.keys())
    if keep_original_user_ids:
        # 원본 사용자 ID 유지 (그대로 사용)
        user_map = {old_id: old_id for old_id in unique_users}
        print(f"  - 원본 사용자 ID 유지 (총 {len(user_map)}명)")
        print(f"  - 사용자 ID 범위: {min(unique_users)} ~ {max(unique_users)}")
    else:
        # 사용자 ID를 1부터 시작하는 연속된 정수로 매핑
        user_map = {old_id: new_id for new_id, old_id in enumerate(unique_users, start=1)}
        print(f"  - 매핑된 사용자 수: {len(user_map)}")
    
    print(f"  - 매핑된 아이템 수: {len(item_map)}")
    
    # 변환된 데이터 쓰기
    print(f"출력 파일 작성 중: {output_file}")
    total_interactions = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for old_user_id in unique_users:
            new_user_id = user_map[old_user_id]
            for item in user_sequences[old_user_id]:
                new_item_id = item_map[item]
                f.write(f"{new_user_id} {new_item_id}\n")
                total_interactions += 1
    
    print(f"변환 완료!")
    print(f"  - 총 상호작용 수: {total_interactions}")
    print(f"  - 출력 파일: {output_file}")
    
    # 매핑 정보 저장 (선택사항)
    mapping_file = output_file.replace('.txt', '_mapping.txt')
    with open(mapping_file, 'w', encoding='utf-8') as f:
        f.write("# 사용자 ID 매핑\n")
        f.write("# 원본_ID -> 새_ID\n")
        for old_id, new_id in sorted(user_map.items()):
            f.write(f"USER: {old_id} -> {new_id}\n")
        
        f.write("\n# 아이템 ID 매핑 (처음 10개만 표시)\n")
        f.write("# 원본_ID -> 새_ID\n")
        for i, (old_id, new_id) in enumerate(sorted(item_map.items(), key=lambda x: x[1])):
            if i < 10:
                f.write(f"ITEM: {old_id} -> {new_id}\n")
            elif i == 10:
                f.write(f"... (총 {len(item_map)}개 아이템)\n")
                break
    
    print(f"  - 매핑 정보: {mapping_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='뉴스 히스토리 데이터를 SASRec 형식으로 변환',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    python prepare_news_dataset.py --input data.tsv --output data/my_dataset.txt
        """
    )
    parser.add_argument('--input', required=True, 
                       help='입력 파일 경로 (TSV 형식: user_id\\titem1 item2 ...)')
    parser.add_argument('--output', required=True, 
                       help='출력 파일 경로 (예: data/my_dataset.txt)')
    parser.add_argument('--keep_original_user_ids', action='store_true', default=False,
                       help='원본 사용자 ID를 그대로 유지 (기본값: False, 1부터 시작하는 새 ID로 매핑)')
    parser.add_argument('--remove_n_prefix', action='store_true', default=False,
                       help='아이템 ID에서 "N" 접두사 제거 (예: N39011 → 39011)')
    
    args = parser.parse_args()
    
    convert_news_to_sasrec(args.input, args.output, args.keep_original_user_ids, args.remove_n_prefix)

